"""
GreenMind Public API - v1
Module: Views (Logic xử lý cho các Endpoint API)

Endpoint Map:
  POST   /api/v1/auth/register/        - Đăng ký tài khoản mới
  GET    /api/v1/auth/profile/         - Xem thông tin & role của mình
  POST   /api/v1/auth/token/           - Đăng nhập, lấy Access + Refresh Token (JWT)
  POST   /api/v1/auth/token/refresh/   - Làm mới Access Token
  POST   /api/v1/auth/token/blacklist/ - Đăng xuất (revoke token)

  GET    /api/v1/forecast/             - Dự báo tồn kho cho 1 SKU
  GET    /api/v1/forecast/compare/     - So sánh 3 mô hình AI cho 1 SKU
  GET    /api/v1/forecast/recommend/   - Lấy gợi ý DSS (Safety Stock, Reorder Point)

  GET    /api/v1/inventory/            - Lấy dữ liệu tồn kho gần nhất
  POST   /api/v1/inventory/transact/   - [Admin Only] Thực hiện nhập/xuất kho qua API

  GET    /api/v1/esg/                  - Lấy báo cáo ESG / Green Metrics

  GET    /api/v1/catalog/              - Lấy danh sách Master Data sản phẩm
  POST   /api/v1/worker/run/           - [Admin Only] Kích hoạt E2E Worker thủ công
"""

import sys, os
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import (
    UserProfileSerializer, UserRegisterSerializer,
    ForecastRequestSerializer, ForecastResultSerializer,
    ForecastCompareSerializer, DSS_RecommendationSerializer,
    InventoryTransactionSerializer,
)
from .permissions import IsAdmin, IsManagerOrAbove, IsAnyAuthenticatedUser

logger = logging.getLogger("greenmind.api")

# ─────────────────────────────────────────────────
# Lazy engine loader (tái sử dụng instance từ dashboard)
# ─────────────────────────────────────────────────
# engine is added to sys.path in core/settings.py

try:
    from greenmind_engine import GreenMindEngine
    from controllers.system_controllers import InventoryController, LogisticsController
except ImportError:
    GreenMindEngine = None

from core.utils.error_sanitizer import sanitize_error
from apps.dashboard.views import is_technical_admin

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        if GreenMindEngine is None:
            raise RuntimeError("GreenMindEngine chưa được khởi tạo.")
        _engine = GreenMindEngine(
            server=os.getenv("DB_SERVER", r"DESKTOP-65L3CQO\KMS"),
            database=os.getenv("DB_NAME", "GRW"),
        )
        _engine.load_data()
    return _engine


def _error(request, msg, code=status.HTTP_400_BAD_REQUEST):
    is_tech = is_technical_admin(request.user) if request.user.is_authenticated else False
    sanitized = sanitize_error(msg, is_tech)
    return Response({"success": False, "error": sanitized}, status=code)


def _ok(data, msg="Thành công."):
    return Response({"success": True, "message": msg, "data": data})


# ═══════════════════════════════════════════════════
# CORE VIEWS
# ═══════════════════════════════════════════════════

class ApiIndexView(APIView):
    """
    GET /api/v1/
    Index của API, liệt kê các phân vùng module khả dụng.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return _ok({
            "version": "1.0.0",
            "name": "GreenMind AI Core API",
            "modules": {
                "auth": "/api/v1/auth/",
                "forecast": "/api/v1/forecast/",
                "inventory": "/api/v1/inventory/",
                "catalog": "/api/v1/catalog/",
                "esg": "/api/v1/esg/",
                "worker": "/api/v1/worker/"
            },
            "docs": "/docs/TECHNICAL_ARCHITECTURE.md",
            "status": "Running"
        }, msg="Chào mừng đến với GreenMind AI v1.")


# ═══════════════════════════════════════════════════
# AUTH VIEWS
# ═══════════════════════════════════════════════════

class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Đăng ký tài khoản mới. Không cần xác thực trước.
    Body: { username, email, first_name, last_name, password, password_confirm, role }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return _ok(
                {"username": user.username, "role": user.groups.first().name if user.groups.first() else "Viewer"},
                msg=f"Tài khoản '{user.username}' đã được tạo thành công."
            )
        return _error(serializer.errors, status.HTTP_422_UNPROCESSABLE_ENTITY)


class MyProfileView(APIView):
    """
    GET /api/v1/auth/profile/
    Xem thông tin profile và vai trò của người dùng đang đăng nhập.
    """
    permission_classes = [IsAnyAuthenticatedUser]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return _ok(serializer.data)


# ═══════════════════════════════════════════════════
# FORECAST VIEWS (Manager+ required)
# ═══════════════════════════════════════════════════

class ForecastView(APIView):
    """
    GET /api/v1/forecast/?item_id=<id>&days=<30>
    Dự báo tồn kho tương lai cho 1 SKU bằng mô hình Champion.
    Quyền: Manager hoặc Admin.
    """
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        serializer = ForecastRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return _error(request, serializer.errors)
        try:
            engine = _get_engine()
            result = engine.forecast_future(
                item_id=serializer.validated_data["item_id"],
                days=serializer.validated_data["days"],
            )
            # Chuyển đổi numpy types -> native Python để JSON-serializable
            output = {
                "item_id": float(result["itemid"]),
                "model_used": result["model_used"],
                "forecast_dates": [str(d)[:10] for d in result["forecast_dates"]],
                "forecast_values": [round(float(v), 2) for v in result["forecast_values"]],
                "avg_discount_used": round(float(result["avg_discount_used"]), 4),
            }
            return _ok(output)
        except Exception as e:
            logger.error(f"[ForecastView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForecastCompareView(APIView):
    """
    GET /api/v1/forecast/compare/?item_id=<id>
    So sánh kết quả của 3 mô hình SARIMAX, Prophet, XGBoost.
    Trả về bảng MAE/RMSE và tên Champion.
    Quyền: Manager hoặc Admin.
    """
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        item_id = request.query_params.get("item_id")
        if not item_id:
            return _error("Thiếu tham số 'item_id'.")
        try:
            engine = _get_engine()
            result = engine.compare_models(float(item_id))
            battle_list = result["battle_results"].to_dict("records")
            output = {
                "item_id": float(result["itemid"]),
                "champion": result["champion"],
                "battle_results": [
                    {"Model": r["Model"], "MAE": round(r["MAE"], 4), "RMSE": round(r["RMSE"], 4)}
                    for r in battle_list
                ],
                "green_impact": {
                    "annual_co2_kg": round(float(result["green_impact"]["annual_co2_kg"]), 2),
                    "trees_equivalent": round(float(result["green_impact"]["trees_equivalent"]), 2),
                },
            }
            return _ok(output)
        except Exception as e:
            logger.error(f"[ForecastCompareView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendView(APIView):
    """
    GET /api/v1/forecast/recommend/?item_id=<id>
    Lấy gợi ý tồn kho từ hệ thống DSS (Decision Support System).
    Trả về: Safety Stock tối ưu, Reorder Point, Điểm tiết kiệm CO2.
    Quyền: Manager hoặc Admin.
    """
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        item_id = request.query_params.get("item_id")
        if not item_id:
            return _error("Thiếu tham số 'item_id'.")
        try:
            engine = _get_engine()
            ctrl = InventoryController(engine)
            reco = ctrl.get_dss_recommendations(float(item_id))
            output = {
                "champion": reco["champion"],
                "safety_stock_optimized": round(float(reco["safety_stock_optimized"]), 2),
                "reorder_point": round(float(reco["reorder_point"]), 2),
                "lead_time_demand": round(float(reco["lead_time_demand"]), 2),
                "mae_error": round(float(reco["mae_error"]), 4),
                "green_saving_co2_kg_annual": round(float(reco["green_saving"]), 2),
            }
            return _ok(output)
        except Exception as e:
            logger.error(f"[RecommendView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════
# INVENTORY VIEWS
# ═══════════════════════════════════════════════════

class InventoryView(APIView):
    """
    GET /api/v1/inventory/?item_id=<id>&limit=<50>
    Lấy lịch sử tồn kho gần nhất từ SQL Server.
    Quyền: Mọi user đã đăng nhập.
    """
    permission_classes = [IsAnyAuthenticatedUser]

    def get(self, request):
        item_id = request.query_params.get("item_id")
        limit = int(request.query_params.get("limit", 50))
        try:
            import pandas as pd
            engine = _get_engine()
            sql_eng = engine.get_sql_engine()
            if item_id:
                df = pd.read_sql(
                    "SELECT TOP :n * FROM Fact_Inventory_History WHERE ItemID=:id ORDER BY Timestamp DESC",
                    con=sql_eng, params={"n": limit, "id": float(item_id)}
                )
            else:
                df = pd.read_sql(
                    f"SELECT TOP {limit} * FROM Fact_Inventory_History ORDER BY Timestamp DESC",
                    con=sql_eng
                )
            records = df.to_dict("records")
            # Chuyển đổi Timestamp sang string
            for r in records:
                if "Timestamp" in r and hasattr(r["Timestamp"], "isoformat"):
                    r["Timestamp"] = r["Timestamp"].isoformat()
            return _ok({"count": len(records), "records": records})
        except Exception as e:
            logger.error(f"[InventoryView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class InventoryTransactView(APIView):
    """
    POST /api/v1/inventory/transact/
    Thực hiện giao dịch Nhập/Xuất kho qua API.
    Body: { item_id, transaction_type: "inbound"|"outbound", quantity, price }
    Quyền: CHỈ ADMIN.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InventoryTransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(request, serializer.errors)
        d = serializer.validated_data
        try:
            from sqlalchemy import text
            engine = _get_engine()
            sql_eng = engine.get_sql_engine()
            user_id = request.user.id or 1

            with sql_eng.begin() as conn:
                if d["transaction_type"] == "outbound":
                    conn.execute(
                        text("EXEC sp_SellProduct @ItemID=:id, @QuantityToSell=:qty, @SellingPrice=:price, @UserID=:uid"),
                        {"id": d["item_id"], "qty": d["quantity"], "price": d["price"], "uid": user_id},
                    )
                    msg = f"Xuất kho thành công: SKU {d['item_id']}, Qty {d['quantity']}."
                else:
                    cur = conn.execute(
                        text("SELECT TOP 1 StockQuantity FROM Fact_Inventory_History WHERE ItemID=:id ORDER BY Timestamp DESC"),
                        {"id": d["item_id"]}
                    ).fetchone()
                    new_stock = (cur[0] if cur else 0) + d["quantity"]
                    conn.execute(
                        text("INSERT INTO Fact_Inventory_History (ItemID, UserID, Timestamp, Price, OriginalPrice, Discount, StockQuantity, SoldQuantity) VALUES (:id, :uid, GETDATE(), :p, :p, 0, :s, 0)"),
                        {"id": d["item_id"], "uid": user_id, "p": d["price"], "s": new_stock},
                    )
                    msg = f"Nhập kho thành công: SKU {d['item_id']}, Qty {d['quantity']}, Tồn mới: {new_stock}."

            # Reload engine cache
            engine.load_data()
            return _ok({"item_id": d["item_id"], "new_transaction_type": d["transaction_type"]}, msg=msg)
        except Exception as e:
            logger.error(f"[InventoryTransactView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════
# ESG VIEW
# ═══════════════════════════════════════════════════

class ESGView(APIView):
    """
    GET /api/v1/esg/
    Lấy tổng hợp báo cáo ESG và Green Metrics của toàn bộ kho.
    Quyền: Mọi user đã đăng nhập.
    """
    permission_classes = [IsAnyAuthenticatedUser]

    def get(self, request):
        try:
            engine = _get_engine()
            esg = engine.get_esg_metrics()
            output = {
                "actual_waste_kg": round(float(esg["actual_waste_kg"]), 2),
                "total_co2_saving_kg_annual": round(float(esg["total_co2_saving"]), 2),
                "trees_equivalent": round(float(esg["total_trees"]), 2),
                "quarterly_trend": esg["trend_df"].to_dict("records"),
            }
            return _ok(output)
        except Exception as e:
            logger.error(f"[ESGView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════
# CATALOG VIEW
# ═══════════════════════════════════════════════════

class CatalogView(APIView):
    """
    GET /api/v1/catalog/
    Lấy danh sách toàn bộ sản phẩm (Master Data) từ Dim_Products.
    Quyền: Mọi user đã đăng nhập.
    """
    permission_classes = [IsAnyAuthenticatedUser]

    def get(self, request):
        try:
            import pandas as pd
            engine = _get_engine()
            sql_eng = engine.get_sql_engine()
            df = pd.read_sql(
                "SELECT ItemID, ProductName, Category, Unit, EmissionFactor, SafetyStockLevel "
                "FROM Dim_Products WHERE IsActive = 1 ORDER BY ItemID",
                con=sql_eng,
            )
            records = df.to_dict("records")
            return _ok({"count": len(records), "products": records})
        except Exception as e:
            logger.error(f"[CatalogView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════
# E2E WORKER VIEW (Admin Only)
# ═══════════════════════════════════════════════════

class WorkerRunView(APIView):
    """
    POST /api/v1/worker/run/
    Kích hoạt thủ công E2E Worker:
      1. Chạy lại so sánh mô hình cho mọi SKU.
      2. Đồng bộ Safety Stock tối ưu từ AI về SQL Server.
    Quyền: CHỈ ADMIN.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        try:
            engine = _get_engine()
            sku_list = engine.df["itemid"].unique().tolist()
            results = []
            errors = []

            for sku in sku_list:
                try:
                    new_ss = engine.sync_safety_stock_to_db(sku)
                    results.append({"sku": float(sku), "new_safety_stock": round(new_ss, 2), "status": "OK"})
                except Exception as e:
                    errors.append({"sku": float(sku), "error": str(e)})

            # Reload engine sau khi đồng bộ
            engine.load_data()

            return _ok(
                {"updated": len(results), "failed": len(errors), "details": results, "errors": errors},
                msg=f"E2E Worker hoàn tất: {len(results)} SKU đã đồng bộ, {len(errors)} lỗi."
            )
        except Exception as e:
            logger.error(f"[WorkerRunView] {e}")
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuditLogView(APIView):
    """
    GET /api/v1/audit/
    [Admin Only] Xem nhật ký thao tác quản trị từ Admin_Action_Logs.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            import pandas as pd
            engine = _get_engine()
            sql_eng = engine.get_sql_engine()
            limit = int(request.query_params.get("limit", 100))
            
            df = pd.read_sql(
                f"SELECT TOP {limit} * FROM Admin_Action_Logs ORDER BY Timestamp DESC",
                con=sql_eng
            )
            records = df.to_dict("records")
            for r in records:
                if r.get("Timestamp") and hasattr(r["Timestamp"], "isoformat"):
                    r["Timestamp"] = r["Timestamp"].isoformat()
                    
            return _ok({"count": len(records), "logs": records})
        except Exception as e:
            return _error(request, e, status.HTTP_500_INTERNAL_SERVER_ERROR)
