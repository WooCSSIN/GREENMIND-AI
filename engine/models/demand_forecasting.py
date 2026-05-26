"""
Module: Time-series Forecasting cho Dự án GREENMIND
Tác giả: GREENMIND Research Team
Mô tả:
    Module này thực hiện dự báo nhu cầu sản phẩm dựa trên lịch sử bán hàng
    sử dụng các mô hình: ARIMA, SARIMA, và Prophet (Facebook)

Mục tiêu Green:
    - Giảm tồn kho dư thừa (overstocking) -> Giảm lãng phí tài nguyên
    - Tối ưu nhập hàng dựa trên dự báo chính xác -> Tiết kiệm năng lượng vận chuyển
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from sklearn.metrics import mean_absolute_error, mean_squared_error

import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")


class DemandForecaster:
    """
    Class chính để dự báo nhu cầu sản phẩm
    """

    def __init__(self, data_path):
        """
        Parameters:
        -----------
        data_path : str
            Đường dẫn tới file Price_Stock_History.csv
        """
        self.data_path = data_path
        self.df = None
        self.product_data = {}
        self.models = {}
        self.predictions = {}

    def load_data(self):
        """Đọc và chuẩn bị dữ liệu"""
        print(f"📂 Đang đọc dữ liệu từ: {self.data_path}")
        self.df = pd.read_csv(self.data_path, encoding="utf-8-sig")

        self.df["timestamp"] = pd.to_datetime(self.df["time_str"])
        self.df = self.df.sort_values("timestamp")

        print(f"✓ Đã tải {len(self.df)} dòng dữ liệu")
        print(
            f"✓ Khoảng thời gian: {self.df['timestamp'].min()} → {self.df['timestamp'].max()}"
        )
        print(f"✓ Số sản phẩm: {self.df['itemid'].nunique()}")

        return self.df

    def prepare_product_series(self, item_id, resample_freq="D"):
        """
        Chuẩn bị chuỗi thời gian cho 1 sản phẩm

        Parameters:
        -----------
        item_id : str
            ID sản phẩm
        resample_freq : str
            Tần suất lấy mẫu: 'D' (ngày), 'W' (tuần), 'M' (tháng)

        Returns:
        --------
        pd.Series : Chuỗi thời gian số lượng bán
        """
        product_df = self.df[self.df["itemid"] == item_id].copy()

        if len(product_df) == 0:
            print(f"⚠ Không có dữ liệu cho sản phẩm {item_id}")
            return pd.Series(dtype=float)

        product_df.set_index("timestamp", inplace=True)

        ts = product_df["sold"].resample(resample_freq).last()

        ts = ts.ffill()

        ts_diff = ts.diff().dropna()

        ts_diff = ts_diff[ts_diff >= 0]

        if len(ts_diff) == 0:
            print(f"⚠ Không thể tính diff, sử dụng dữ liệu gốc")
            ts_diff = ts.copy()

        self.product_data[item_id] = {"series": ts_diff, "full_data": product_df}

        return ts_diff

    def select_best_product(self, min_datapoints=30):
        """
        Chọn sản phẩm có dữ liệu tốt nhất để demo

        Parameters:
        -----------
        min_datapoints : int
            Số điểm dữ liệu tối thiểu

        Returns:
        --------
        str : ItemID của sản phẩm phù hợp
        """
        product_scores = {}

        for item_id in self.df["itemid"].unique():
            product_df = self.df[self.df["itemid"] == item_id]

            score = len(product_df)
            product_scores[item_id] = score

        sorted_products = sorted(
            product_scores.items(), key=lambda x: x[1], reverse=True
        )

        for item_id, score in sorted_products:
            series = self.prepare_product_series(item_id, resample_freq="D")
            if len(series) >= min_datapoints:
                print(f"✓ Đã chọn sản phẩm {item_id} với {len(series)} điểm dữ liệu")
                return item_id

        return sorted_products[0][0]

    def check_stationarity(self, series, name="Series"):
        """
        Kiểm tra tính dừng (Stationarity) bằng ADF Test

        Returns:
        --------
        bool : True nếu chuỗi dừng
        """
        result = adfuller(series.dropna(), autolag="AIC")

        print(f"\n--- ADF Test: {name} ---")
        print(f"ADF Statistic: {result[0]:.4f}")
        print(f"p-value: {result[1]:.4f}")
        print(f"Critical Values:")
        for key, value in result[4].items():
            print(f"  {key}: {value:.4f}")

        if result[1] <= 0.05:
            print("✓ Chuỗi DỪM (p-value <= 0.05)")
            return True
        else:
            print("✗ Chuỗi KHÔNG DỪM (cần sai phân)")
            return False

    def plot_series(self, item_id, title="Biến động số lượng bán"):
        """Vẽ biểu đồ chuỗi thời gian"""
        if item_id not in self.product_data:
            raise ValueError(f"Sản phẩm {item_id} chưa được chuẩn bị!")

        series = self.product_data[item_id]["series"]

        plt.figure(figsize=(14, 5))
        plt.plot(series.index, series.values, marker="o", linestyle="-", markersize=3)
        plt.title(title, fontsize=14, fontweight="bold")
        plt.xlabel("Thời gian")
        plt.ylabel("Số lượng bán")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def split_train_test(self, item_id, test_size=0.2):
        """
        Chia dữ liệu train/test

        Parameters:
        -----------
        test_size : float
            Tỷ lệ dữ liệu test (0-1)

        Returns:
        --------
        tuple : (train_series, test_series)
        """
        series = self.product_data[item_id]["series"]
        split_idx = int(len(series) * (1 - test_size))

        train = series.iloc[:split_idx]
        test = series.iloc[split_idx:]

        print(f"\n📊 Chia dữ liệu:")
        print(f"  Train: {len(train)} điểm ({train.index[0]} → {train.index[-1]})")
        print(f"  Test:  {len(test)} điểm ({test.index[0]} → {test.index[-1]})")

        return train, test

    def fit_arima(self, item_id, order=(1, 1, 1), seasonal_order=None):
        """
        Huấn luyện mô hình ARIMA/SARIMA

        Parameters:
        -----------
        order : tuple (p, d, q)
            Bậc của ARIMA
        seasonal_order : tuple (P, D, Q, s) hoặc None
            Bậc của phần mùa vụ (nếu có)

        Returns:
        --------
        Fitted model
        """
        train, test = self.split_train_test(item_id)

        print(f"\n🤖 Training {'SARIMA' if seasonal_order else 'ARIMA'}{order}...")

        try:
            if seasonal_order:
                model = SARIMAX(train, order=order, seasonal_order=seasonal_order)
            else:
                model = ARIMA(train, order=order)

            fitted_model = model.fit(disp=False)

            forecast = fitted_model.forecast(steps=len(test))

            mae = mean_absolute_error(test, forecast)
            rmse = np.sqrt(mean_squared_error(test, forecast))

            print(f"✓ Training hoàn tất!")
            print(f"  MAE:  {mae:.2f}")
            print(f"  RMSE: {rmse:.2f}")

            self.models[item_id] = fitted_model
            self.predictions[item_id] = {
                "train": train,
                "test": test,
                "forecast": forecast,
                "mae": mae,
                "rmse": rmse,
            }

            return fitted_model

        except Exception as e:
            print(f"❌ Lỗi khi training: {e}")
            return None

    def plot_forecast(self, item_id):
        """Vẽ biểu đồ so sánh giữa thực tế và dự báo"""
        if item_id not in self.predictions:
            raise ValueError(f"Chưa có dự báo cho sản phẩm {item_id}")

        pred = self.predictions[item_id]

        plt.figure(figsize=(14, 6))

        plt.plot(
            pred["train"].index,
            pred["train"].values,
            label="Train Data",
            color="blue",
            alpha=0.6,
        )

        plt.plot(
            pred["test"].index,
            pred["test"].values,
            label="Test Data (Actual)",
            color="green",
            marker="o",
            markersize=5,
        )

        plt.plot(
            pred["test"].index,
            pred["forecast"].values,
            label="Forecast",
            color="red",
            linestyle="--",
            marker="x",
            markersize=5,
        )

        plt.title(
            f"Dự báo nhu cầu - Sản phẩm {item_id}", fontsize=14, fontweight="bold"
        )
        plt.xlabel("Thời gian")
        plt.ylabel("Số lượng bán")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        print(f"\n📈 Đánh giá mô hình:")
        print(f"  MAE:  {pred['mae']:.2f} (trung bình sai số tuyệt đối)")
        print(f"  RMSE: {pred['rmse']:.2f} (căn bậc 2 trung bình bình phương sai số)")

    def forecast_future(self, item_id, days=14):
        """
        Dự báo nhu cầu cho N ngày tới

        Parameters:
        -----------
        days : int
            Số ngày muốn dự báo

        Returns:
        --------
        pd.Series : Kết quả dự báo
        """
        if item_id not in self.models:
            raise ValueError(f"Chưa train mô hình cho sản phẩm {item_id}")

        model = self.models[item_id]
        future_forecast = model.forecast(steps=days)

        print(f"\n🔮 Dự báo {days} ngày tới cho sản phẩm {item_id}:")
        print(future_forecast)

        return future_forecast


if __name__ == "__main__":

    print("=" * 60)
    print("GREENMIND - Demand Forecasting Module")
    print("=" * 60)

    forecaster = DemandForecaster(
        data_path=r"D:\GREENMIND\data\processed\Price_Stock_History.csv"
    )

    df = forecaster.load_data()

    sample_item = forecaster.select_best_product(min_datapoints=30)
    print(f"\n🎯 Sản phẩm được chọn: {sample_item}")

    series = forecaster.product_data[sample_item]["series"]
    print(
        f"✓ Chuỗi thời gian: {len(series)} điểm dữ liệu ({series.index[0].date()} → {series.index[-1].date()})"
    )

    forecaster.check_stationarity(series, name=f"Product {sample_item}")

    forecaster.plot_series(sample_item)

    model = forecaster.fit_arima(sample_item, order=(2, 1, 2))

    if model:
        forecaster.plot_forecast(sample_item)

        future = forecaster.forecast_future(sample_item, days=14)
