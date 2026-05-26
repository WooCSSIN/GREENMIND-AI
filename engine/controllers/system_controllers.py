"""
GreenMind System Controllers - v2.0
====================================
Changelog v2.0:
  - Fix #5: LogisticsController redesigned as proper integration layer.
            Standard payload/response contract.
            Toggle VROUTE_ENABLED=true in .env to call live API.
"""

import hashlib
import os
import logging
from datetime import datetime

logger = logging.getLogger("greenmind.controllers")


class AuthController:
    """
    Quản lý xác thực người dùng qua bảng Dim_Users trên SQL Server.
    (Lớp Legacy - Hệ thống hiện dùng Django Auth/SQLite cho Web session)
    """

    def __init__(self, engine):
        self.engine = engine

    def _ensure_user_table_exists(self):
        sql_eng = self.engine.get_sql_engine()
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Dim_Users')
        BEGIN
            CREATE TABLE Dim_Users (
                UserID INT IDENTITY(1,1) PRIMARY KEY,
                Username NVARCHAR(50) UNIQUE NOT NULL,
                PasswordHash NVARCHAR(255) NOT NULL,
                FullName NVARCHAR(100),
                Email NVARCHAR(100),
                PhoneNumber NVARCHAR(20),
                DateOfBirth DATE,
                Role NVARCHAR(20) DEFAULT 'Admin',
                CreatedAt DATETIME DEFAULT GETDATE()
            );
        END
        """
        with sql_eng.begin() as conn:
            from sqlalchemy import text
            conn.execute(text(create_table_sql))

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        self._ensure_user_table_exists()
        sql_eng = self.engine.get_sql_engine()
        pw_hash = self._hash_password(password)
        with sql_eng.connect() as conn:
            from sqlalchemy import text
            user = conn.execute(
                text("SELECT * FROM Dim_Users WHERE Username = :u AND PasswordHash = :p"),
                {"u": username, "p": pw_hash},
            ).fetchone()
            return (True, user) if user else (False, "Tài khoản hoặc mật khẩu không chính xác.")

    def register(self, username, password, full_name, email=None, phone=None, dob=None):
        self._ensure_user_table_exists()
        sql_eng = self.engine.get_sql_engine()
        pw_hash = self._hash_password(password)
        try:
            with sql_eng.begin() as conn:
                from sqlalchemy import text
                conn.execute(
                    text("""
                        INSERT INTO Dim_Users (Username, PasswordHash, FullName, Email, PhoneNumber, DateOfBirth)
                        VALUES (:u, :p, :f, :e, :ph, :d)
                    """),
                    {"u": username, "p": pw_hash, "f": full_name, "e": email, "ph": phone, "d": dob},
                )
            return True, "Đăng ký thành công."
        except Exception as e:
            return False, f"Lỗi CSDL: {str(e)}"


class InventoryController:
    """
    Điều phối hoạt động nghiệp vụ Tồn kho & AI.
    """

    def __init__(self, engine):
        self.engine = engine

    def process_feedback_loop(self, item_id):
        """Đẩy Safety Stock tối ưu từ AI vào SQL Server."""
        try:
            new_ss = self.engine.sync_safety_stock_to_db(item_id)
            return True, f"Đã đồng bộ Safety Stock = {new_ss:.1f} vào hệ thống."
        except Exception as e:
            return False, f"Lỗi feedback loop: {str(e)}"

    def get_dss_recommendations(self, item_id):
        """Lấy gợi ý DSS (Safety Stock, ROP, Green Saving)."""
        return self.engine.get_inventory_recommendation(item_id)


class LogisticsController:
    """
    Integration Layer kết nối với Abivin vRoute API.

    Cấu hình qua .env:
      VROUTE_ENABLED=false    → Mock mode (mặc định, không cần API key)
      VROUTE_ENABLED=true     → Gọi API thật
      VROUTE_API_KEY=<key>    → API key từ Abivin
      VROUTE_API_URL=<url>    → Base URL (mặc định: https://api.abivin.com/v1)

    Response contract (chuẩn):
      {
        "success": bool,
        "order_id": str,
        "mode": "live" | "mock",
        "payload_sent": dict,
        "response": dict | None,
        "message": str
      }
    """

    VROUTE_API_URL_DEFAULT = "https://api.abivin.com/v1/orders"

    def __init__(self, engine):
        self.engine  = engine
        self.enabled = os.getenv("VROUTE_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("VROUTE_API_KEY", "")
        self.api_url = os.getenv("VROUTE_API_URL", self.VROUTE_API_URL_DEFAULT)

    def _build_payload(self, item_id: float, quantity: float, metadata: dict = None) -> dict:
        """
        Xây dựng chuẩn payload theo định dạng Abivin vRoute.
        """
        order_id = f"GM-{int(item_id)}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "order_id":           order_id,
            "sku":                int(item_id),
            "quantity":           quantity,
            "demand_forecast":    quantity,
            "priority":           "HIGH" if quantity > 100 else "NORMAL",
            "warehouse_location": {
                "name": "GreenMind Warehouse HCM",
                "lat":  10.7769,
                "lng":  106.7009,
            },
            "requested_at":       datetime.now().isoformat(),
            **(metadata or {}),
        }

    def _mock_response(self, payload: dict) -> dict:
        """Trả về response giả lập khi ở chế độ Mock."""
        return {
            "success":      True,
            "order_id":     payload["order_id"],
            "mode":         "mock",
            "payload_sent": payload,
            "response":     {
                "status":          "ACCEPTED",
                "estimated_eta":   "2h",
                "route_optimized": True,
                "co2_route_kg":    round(payload["quantity"] * 0.012, 3),
            },
            "message": f"[MOCK] Lệnh điều phối SKU {payload['sku']} đã ghi nhận thành công.",
        }

    def _live_request(self, payload: dict) -> dict:
        """Gọi API thật tới Abivin vRoute."""
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type":  "application/json",
            }
            resp = requests.post(
                self.api_url, json=payload, headers=headers, timeout=10
            )
            resp.raise_for_status()
            return {
                "success":      True,
                "order_id":     payload["order_id"],
                "mode":         "live",
                "payload_sent": payload,
                "response":     resp.json(),
                "message":      f"Lệnh điều phối SKU {payload['sku']} đã gửi tới Abivin vRoute thành công.",
            }
        except Exception as e:
            logger.error(f"[vRoute] Lỗi gọi API: {e}")
            return {
                "success":      False,
                "order_id":     payload.get("order_id", "unknown"),
                "mode":         "live",
                "payload_sent": payload,
                "response":     None,
                "message":      f"Lỗi gọi vRoute API: {str(e)}",
            }

    def send_to_vroute(self, item_id: float, quantity: float, metadata: dict = None) -> dict:
        """
        Gửi lệnh điều phối tới Abivin vRoute.
        Tự động chọn Mock hoặc Live dựa trên VROUTE_ENABLED.
        """
        payload = self._build_payload(item_id, quantity, metadata)
        logger.info(f"[vRoute] order_id={payload['order_id']} | mode={'live' if self.enabled else 'mock'}")

        if self.enabled and self.api_key:
            return self._live_request(payload)
        return self._mock_response(payload)
