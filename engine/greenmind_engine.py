"""
GreenMind AI Core Engine - v2.0
====================================
Changelog v2.0:
  - Fix #1: Chuyển pipeline dự báo từ Stock sang Demand (sold_qty delta).
             Công thức Safety Stock và ROP chuẩn nghiệp vụ dùng sigma_demand.
  - Fix #2: CO₂ Saving theo mô hình năng lượng kho (overstock→kWh→kgCO₂e).
             Fallback demo nếu dữ liệu năng lượng không đủ.
"""

import os
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
from prophet import Prophet
import xgboost as xgb
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy import text

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# Hệ số môi trường (tuỳ chỉnh qua .env)
# STORAGE_KWH_PER_UNIT_PER_DAY: điện tiêu thụ để lưu 1 đơn vị hàng/ngày
# GRID_EMISSION_VN:              hệ số phát thải lưới điện Việt Nam 2024 (EVN)
# ─────────────────────────────────────────────────────────────
STORAGE_KWH_PER_UNIT = float(os.getenv("STORAGE_KWH_PER_UNIT", "0.002"))
GRID_EMISSION_VN     = float(os.getenv("GRID_EMISSION_VN", "0.4937"))
EMISSION_FACTOR_DEMO = float(os.getenv("EMISSION_FACTOR_DEMO", "0.85"))  # fallback


class GreenMindEngine:
    def __init__(self, server=None, database=None):
        # Ưu tiên đọc từ tham số truyền vào, nếu không có thì đọc từ .env
        self.server   = server or os.getenv("DB_SERVER", r"DESKTOP-65L3CQO\KMS")
        self.database = database or os.getenv("DB_NAME", "GRW")
        self.df       = None

    # ─────────────────────────────────────────────────────────
    # DATABASE
    # ─────────────────────────────────────────────────────────

    def get_sql_engine(self):
        import pyodbc
        from sqlalchemy import create_engine

        drivers     = list(pyodbc.drivers())
        driver_name = "SQL Server"
        for d in ["ODBC Driver 17 for SQL Server",
                  "ODBC Driver 13 for SQL Server",
                  "SQL Server Native Client 11.0"]:
            if d in drivers:
                driver_name = d
                break

        conn_str = (
            f"mssql+pyodbc://@{self.server}/{self.database}"
            f"?driver={driver_name.replace(' ', '+')}&Trusted_Connection=yes"
        )
        return create_engine(conn_str)

    def load_data(self):
        """Tải dữ liệu lịch sử từ SQL Server. Chỉ lấy SKU đang Active."""
        try:
            sql_engine = self.get_sql_engine()
            # Join với Dim_Products để filter IsActive=1
            query = """
                SELECT h.*
                FROM Fact_Inventory_History h
                JOIN Dim_Products p ON h.ItemID = p.ItemID
                WHERE p.IsActive = 1
                ORDER BY h.Timestamp ASC
            """
            self.df = pd.read_sql(query, con=sql_engine)

            if self.df is not None and not self.df.empty:
                self.df = self.df.rename(columns={
                    "ItemID":        "itemid",
                    "Timestamp":     "timestamp",
                    "Price":         "price",
                    "OriginalPrice": "original_price",
                    "Discount":      "discount",
                    "StockQuantity": "stock",
                    "SoldQuantity":  "sold_qty",
                })
                self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
                return self.df
            else:
                self.df = pd.DataFrame(columns=["itemid", "timestamp", "price", "original_price", "discount", "stock", "sold_qty"])
        except Exception as e:
            print(f"❌ Lỗi load_data: {e}")
            self.df = pd.DataFrame(columns=["itemid", "timestamp", "price", "original_price", "discount", "stock", "sold_qty"])
            return self.df

    def get_sku_names(self):
        """Lấy mapping ItemID → ProductName, chỉ SKU đang Active."""
        try:
            sql_engine = self.get_sql_engine()
            query = "SELECT ItemID, ProductName FROM Dim_Products WHERE IsActive = 1"
            names_df = pd.read_sql(query, con=sql_engine)
            return {str(int(row["ItemID"])): row["ProductName"]
                    for _, row in names_df.iterrows()}
        except Exception as e:
            print(f"Error fetching SKU names: {e}")
            return {}

    # ─────────────────────────────────────────────────────────
    # DATA PREPARATION — Fix #1: Demand-based pipeline
    # ─────────────────────────────────────────────────────────

    def get_product_data(self, item_id):
        """
        Chuẩn bị time-series theo ngày cho 1 SKU.
        - stock : tồn kho tuyệt đối (dùng cho hiển thị, trigger)
        - demand: lượng bán ra thực tế mỗi ngày (mục tiêu dự báo AI)
        demand = sold_qty delta hoặc sold_qty trực tiếp nếu mỗi ngày 1 bản ghi
        """
        if not item_id or self.df is None or self.df.empty:
            return pd.DataFrame()

        # Đảm bảo đồng nhất kiểu dữ liệu (tránh lỗi str vs int64)
        try:
            item_id_numeric = int(item_id)
            p_df = self.df[self.df["itemid"].astype(int) == item_id_numeric].copy()
        except (ValueError, TypeError):
            p_df = self.df[self.df["itemid"].astype(str) == str(item_id)].copy()

        # Resample về ngày: stock = last, sold_qty = sum trong ngày
        daily = (
            p_df.resample("D", on="timestamp")
            .agg(
                stock    =("stock",    "last"),    # tồn kho cuối ngày
                sold_qty =("sold_qty", "sum"),     # tổng bán trong ngày
                discount =("discount", "mean"),
                price    =("price",    "mean"),
            )
            .ffill()
            .reset_index()
        )

        # Đảm bảo có dữ liệu của ngày hôm nay (hiển thị điểm cuối cùng tức thời)
        if not p_df.empty:
            latest_row = p_df.sort_values("timestamp").iloc[-1]
            latest_ts = latest_row["timestamp"]
            latest_date_normalized = latest_ts.normalize()
            
            # Ghi đè hoặc thêm điểm cuối cùng của ngày hôm nay để phản ánh Stock mới nhất
            if latest_date_normalized in daily["timestamp"].values:
                idx = daily[daily["timestamp"] == latest_date_normalized].index[0]
                daily.at[idx, "stock"] = latest_row["stock"]
            else:
                new_row = pd.DataFrame({
                    "timestamp": [latest_date_normalized],
                    "stock": [latest_row["stock"]],
                    "sold_qty": [latest_row["sold_qty"]],
                    "discount": [latest_row["discount"]],
                    "price": [latest_row["price"]],
                })
                daily = pd.concat([daily, new_row], ignore_index=True).sort_values("timestamp")

        # Demand = sold_qty nếu đã là delta; nếu sold_qty tích lũy thì lấy diff
        # Phát hiện tích lũy: nếu sold_qty chỉ tăng không giảm → là tích lũy
        if daily["sold_qty"].is_monotonic_increasing and daily["sold_qty"].max() > 0:
            daily["demand"] = daily["sold_qty"].diff().clip(lower=0).fillna(0)
        else:
            daily["demand"] = daily["sold_qty"].clip(lower=0)

        # Đảm bảo không có NaN
        daily["demand"] = daily["demand"].fillna(0)
        daily["stock"]  = daily["stock"].ffill().fillna(0)
        daily["discount"] = daily["discount"].fillna(0)

        return daily

    # ─────────────────────────────────────────────────────────
    # AI MODELS — target = demand (Fix #1)
    # ─────────────────────────────────────────────────────────

    def run_sarimax(self, train, test):
        """SARIMAX dự báo demand với exog = discount."""
        model = SARIMAX(
            train["demand"],
            exog=train[["discount"]],
            order=(1, 0, 1),
            trend="c",
            enforce_stationarity=False,
        )
        fit  = model.fit(disp=False)
        pred = fit.forecast(len(test), exog=test[["discount"]])
        return np.clip(pred.values, 0, None)

    def run_prophet(self, train, test):
        """Prophet dự báo demand với regressor discount."""
        p_train = train.rename(columns={"timestamp": "ds", "demand": "y"})
        m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        m.add_regressor("discount", prior_scale=0.1)
        m.fit(p_train[["ds", "y", "discount"]])
        future = test.rename(columns={"timestamp": "ds"})[["ds", "discount"]]
        forecast = m.predict(future)
        return np.clip(forecast["yhat"].values, 0, None)

    def run_xgboost(self, train, test):
        """XGBoost dự báo demand với time-based features."""
        def _feats(d):
            d = d.copy()
            d["dow"]       = d["timestamp"].dt.dayofweek
            d["month"]     = d["timestamp"].dt.month
            d["day"]       = d["timestamp"].dt.day
            d["trend_idx"] = d["timestamp"].astype(np.int64) // 10**9
            return d.reset_index(drop=True)

        x_train = _feats(train)
        x_test  = _feats(test)
        features = ["discount", "dow", "month", "day", "trend_idx"]
        model = xgb.XGBRegressor(
            n_estimators=100, objective="reg:absoluteerror", learning_rate=0.05
        )
        model.fit(x_train[features], x_train["demand"])
        return np.clip(model.predict(x_test[features]), 0, None)

    def calculate_metrics(self, actual, predicted):
        mae  = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        return mae, rmse

    # ─────────────────────────────────────────────────────────
    # CO₂ SAVING — Fix #2: Energy-based model
    # ─────────────────────────────────────────────────────────

    def _calc_co2_saving(self, overstock_units_reduced: float, mae_saving_fallback: float) -> float:
        """
        Tính CO₂ tiết kiệm theo mô hình năng lượng kho.

        Công thức chính:
            kWh_saved     = overstock_reduced × STORAGE_KWH_PER_UNIT × 365
            kgCO2e_saved  = kWh_saved × GRID_EMISSION_VN

        Fallback (demo): nếu overstock_units_reduced <= 0 hoặc thiếu dữ liệu
            kgCO2e_saved  = mae_saving_fallback × EMISSION_FACTOR_DEMO × 12
        """
        if overstock_units_reduced > 0:
            kwh_saved    = overstock_units_reduced * STORAGE_KWH_PER_UNIT * 365
            return kwh_saved * GRID_EMISSION_VN
        else:
            # fallback demo khi không đủ dữ liệu năng lượng
            return max(mae_saving_fallback * EMISSION_FACTOR_DEMO * 12, 0.01)

    # ─────────────────────────────────────────────────────────
    # CORE METHODS
    # ─────────────────────────────────────────────────────────

    def compare_models(self, item_id, test_size=0.2):
        """
        Battle of Models: SARIMAX vs Prophet vs XGBoost.
        Target: demand (sold_qty per day).
        Green Impact tính theo mô hình năng lượng kho (Fix #2).
        """
        data      = self.get_product_data(item_id)
        split_idx = int(len(data) * (1 - test_size))
        train, test = data.iloc[:split_idx], data.iloc[split_idx:]

        # Ngăn chặn lỗi khi data quá ít (ví dụ SKU chỉ có 1-2 ngày dữ liệu)
        if len(train) < 2 or len(test) < 1:
            actual = test["demand"].values if len(test) > 0 else np.array([0])
            fallback_pred = np.zeros(len(actual))
            results = {"SARIMAX": fallback_pred, "Prophet": fallback_pred, "XGBoost": fallback_pred}
        else:
            actual = test["demand"].values
            results = {
                "SARIMAX": self.run_sarimax(train, test),
                "Prophet": self.run_prophet(train, test),
                "XGBoost": self.run_xgboost(train, test),
            }

        metrics = []
        for m_name, pred in results.items():
            mae, rmse = self.calculate_metrics(actual, pred)
            metrics.append({"Model": m_name, "MAE": mae, "RMSE": rmse, "Predictions": pred})

        battle_df  = pd.DataFrame(metrics).sort_values("MAE")
        best_model = battle_df.iloc[0]

        # Tính tiết kiệm CO₂ theo Fix #2
        train_mean = train["demand"].mean() if len(train) > 0 else 0
        naive_mae       = mean_absolute_error(actual, np.full(len(actual), train_mean))
        mae_saving      = max(naive_mae - best_model["MAE"], 0)

        # overstock_reduced = số đơn vị hàng tồn dư giảm được nhờ AI
        avg_stock       = train["stock"].mean()
        avg_demand      = train["demand"].mean()
        opt_safety      = 1.65 * best_model["MAE"] * np.sqrt(3)  # 3-day lead time
        overstock_now   = max(avg_stock - avg_demand * 3, 0)
        overstock_opt   = opt_safety
        overstock_delta = max(overstock_now - overstock_opt, 0)

        ann_co2 = self._calc_co2_saving(overstock_delta, mae_saving)
        trees_eq = ann_co2 / 20

        # ---- GHI LOG XUỐNG CSDL (Green_Impact_Logs) ----
        try:
            sql_eng = self.get_sql_engine()
            with sql_eng.begin() as conn:
                conn.execute(
                    text("INSERT INTO Green_Impact_Logs (ItemID, AnualCO2Saving, TreesEquivalent, ChampionModel) "
                         "VALUES (:id, :co2, :trees, :model)"),
                    {"id": int(item_id), "co2": ann_co2, "trees": trees_eq, "model": str(best_model["Model"])}
                )
        except Exception as e:
            print(f"[Engine] Lỗi ghi log Green_Impact_Logs: {e}")

        return {
            "itemid":         item_id,
            "battle_results": battle_df[["Model", "MAE", "RMSE"]],
            "champion":       best_model["Model"],
            "actual":         actual,
            "best_pred":      best_model["Predictions"],
            "test_dates":     test["timestamp"].values,
            "green_impact": {
                "annual_co2_kg":    ann_co2,
                "trees_equivalent": trees_eq,
                "kwh_saved":        (overstock_delta * STORAGE_KWH_PER_UNIT * 365)
                                    if overstock_delta > 0 else 0,
                "method":           "energy_model" if overstock_delta > 0 else "demo_fallback",
            },
        }

    def forecast_future(self, item_id, days=30):
        """
        Dự báo demand tương lai bằng Champion model.
        """
        data         = self.get_product_data(item_id)
        comparison   = self.compare_models(item_id)
        champion     = comparison["champion"]

        last_date    = data["timestamp"].max()
        if pd.isna(last_date):
            from datetime import datetime
            last_date = pd.Timestamp(datetime.now().date())
        
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days)
        avg_discount = data["discount"].mean() if not data.empty else 0
        future_df    = pd.DataFrame({
            "timestamp": future_dates,
            "discount":  [avg_discount] * days,
        })

        if len(data) < 2:
            forecast = np.zeros(days)
            if not data.empty:
                last_stock = float(data["stock"].iloc[-1])
                forecast = np.full(days, last_stock) # Dự báo nằm ngang nếu ít data
        elif champion == "SARIMAX":
            forecast = self.run_sarimax(data, future_df)
        elif champion == "Prophet":
            forecast = self.run_prophet(data, future_df)
        else:
            forecast = self.run_xgboost(data, future_df)

        # Xử lý NaN (nếu có)
        forecast = np.nan_to_num(forecast, nan=0.0, posinf=1.0e6, neginf=0.0)

        # Fix Spike 120k: Ghìm dự báo không vượt quá 1.5 lần stock MAX lịch sử để tránh nhiễu
        if not data.empty and len(data) < 14:
            max_hist_stock = data["stock"].max()
            limit = max(max_hist_stock * 1.5, 100)
            forecast = np.clip(forecast, 0, limit)

        # ---- GHI LOG XUỐNG CSDL (Fact_AI_Predictions) ----
        try:
            sql_eng = self.get_sql_engine()
            with sql_eng.begin() as conn:
                for d, val in zip(future_dates, forecast):
                    conn.execute(
                        text("INSERT INTO Fact_AI_Predictions (ItemID, PredictionDate, ForecastedQuantity, ModelUsed) "
                             "VALUES (:id, :date, :qty, :model)"),
                        {"id": int(item_id), "date": d.strftime('%Y-%m-%d'), "qty": float(val), "model": str(champion)}
                    )
        except Exception as e:
            print(f"[Engine] Lỗi ghi log Fact_AI_Predictions: {e}")

        return {
            "itemid":           item_id,
            "model_used":       champion,
            "forecast_dates":   future_dates,
            "forecast_values":  forecast,
            "avg_discount_used": avg_discount,
        }

    def get_inventory_recommendation(self, item_id, lead_time=3, service_level=1.65):
        """
        DSS Recommendation dựa trên demand forecast (Fix #1).

        Công thức chuẩn:
          Safety Stock = Z × σ_demand × √(lead_time)
          ROP          = avg_demand × lead_time + Safety Stock
        """
        data         = self.get_product_data(item_id)
        comparison   = self.compare_models(item_id)
        champion_mae = float(comparison["battle_results"].iloc[0]["MAE"])

        # Độ lệch chuẩn demand thực tế
        std_val = float(data["demand"].std()) if len(data["demand"]) > 1 else 0.0
        sigma_demand = std_val if std_val > 0 else (champion_mae if champion_mae > 0 else 1.0)

        safety_stock      = service_level * sigma_demand * np.sqrt(lead_time)
        avg_daily_demand  = float(data["demand"].mean())
        lead_time_demand  = avg_daily_demand * lead_time
        reorder_point     = lead_time_demand + safety_stock

        return {
            "champion":              comparison["champion"],
            "safety_stock_optimized": safety_stock,
            "reorder_point":         reorder_point,
            "lead_time_demand":      lead_time_demand,
            "avg_daily_demand":      avg_daily_demand,
            "sigma_demand":          sigma_demand,
            "mae_error":             champion_mae,
            "green_saving":          comparison["green_impact"]["annual_co2_kg"],
        }

    def sync_safety_stock_to_db(self, item_id):
        """
        Feedback Loop: Đẩy Safety Stock tối ưu từ AI về SQL Server.
        Chỉ cập nhật SKU đang Active.
        """
        reco     = self.get_inventory_recommendation(item_id)
        new_ss   = float(reco["safety_stock_optimized"])
        clean_id = int(item_id)

        engine = self.get_sql_engine()
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE Dim_Products SET SafetyStockLevel = :ss "
                     "WHERE ItemID = :id AND IsActive = 1"),
                {"ss": new_ss, "id": clean_id},
            )
        return new_ss

    def get_esg_metrics(self):
        """
        ESG Metrics tổng hợp từ:
        1. Lãng phí tồn kho thực tế (Inventory_CO2_Warnings - Trigger Layer)
        2. Tiết kiệm tiềm năng từ AI (dùng energy model, Fix #2)
        """
        if self.df is None:
            self.load_data()

        # 1. Lãng phí thực tế
        actual_waste = 0
        try:
            engine  = self.get_sql_engine()
            warn_df = pd.read_sql(
                "SELECT ISNULL(SUM(ExcessCO2_kg), 0) as total_waste FROM Inventory_CO2_Warnings",
                con=engine,
            )
            actual_waste = float(warn_df["total_waste"].iloc[0])
        except Exception:
            actual_waste = 0

        # 2. Tiết kiệm AI
        sku_list               = self.df["itemid"].unique()
        total_potential_saving = 0
        total_kwh              = 0
        for sku in sku_list:
            try:
                impact = self.compare_models(sku)["green_impact"]
                total_potential_saving += impact["annual_co2_kg"]
                total_kwh              += impact.get("kwh_saved", 0)
            except Exception:
                continue

        total_trees = total_potential_saving / 20

        quarters        = ["Q1", "Q2", "Q3", "Q4"]
        optimized_vals  = [total_potential_saving * f for f in [0.22, 0.24, 0.26, 0.28]]
        baseline_vals   = [v + (actual_waste / 4) for v in optimized_vals]

        trend_data = pd.DataFrame({
            "Thứ tự":                        quarters,
            "Phát thải cơ sở (Gồm lãng phí)": baseline_vals,
            "Phát thải AI (Optimized)":        optimized_vals,
        })

        return {
            "actual_waste_kg":         actual_waste,
            "total_co2_saving":        total_potential_saving,
            "total_trees":             total_trees,
            "total_kwh_saved":         total_kwh,
            "trend_df":                trend_data,
        }


if __name__ == "__main__":
    engine = GreenMindEngine()
    engine.load_data()

    sku = engine.df["itemid"].iloc[0]
    res = engine.compare_models(sku)
    print(f"Champion for {res['itemid']}: {res['champion']}")
    print(f"CO₂ Saving : {res['green_impact']['annual_co2_kg']:.2f} kg/năm "
          f"({res['green_impact']['method']})")

    reco = engine.get_inventory_recommendation(sku)
    print(f"Safety Stock: {reco['safety_stock_optimized']:.1f} units")
    print(f"Reorder Point: {reco['reorder_point']:.1f} units")
