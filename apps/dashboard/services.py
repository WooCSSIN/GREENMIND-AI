"""
GreenMind Dashboard - Services
Business logic layer - tách riêng khỏi Views để dễ test và maintain
"""

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from sqlalchemy import text
from .models import UserProfile
import logging

logger = logging.getLogger('security')


class AuthService:
    """
    Service xử lý authentication logic.
    Thay thế dual authentication (Django + SQL Server) bằng single Django auth.
    """
    
    @staticmethod
    @transaction.atomic
    def register_user(username, password, email, fullname, phone, date_of_birth):
        """
        Đăng ký user mới.
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu (plain text, sẽ được hash tự động bằng PBKDF2)
            email: Email
            fullname: Họ và tên
            phone: Số điện thoại
            date_of_birth: Ngày sinh
        
        Returns:
            tuple: (user, error_message)
                - user: User object nếu thành công, None nếu lỗi
                - error_message: None nếu thành công, string nếu lỗi
        """
        try:
            # Tạo Django User (password tự động hash bằng PBKDF2 - secure)
            user = User.objects.create_user(
                username=username,
                password=password,  # Django tự động hash
                email=email
            )
            
            # Tạo hoặc update Profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.fullname = fullname
            profile.phone = phone
            profile.date_of_birth = date_of_birth
            profile.save()
            
            # Log success
            logger.info(f"USER_REGISTERED: {username} (Email: {email})")
            
            return user, None
            
        except Exception as e:
            logger.error(f"REGISTRATION_ERROR: {username} - {str(e)}")
            return None, str(e)
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Xác thực user bằng Django authentication (chuẩn, secure).
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu (plain text)
        
        Returns:
            User object nếu thành công, None nếu thất bại
        """
        user = authenticate(username=username, password=password)
        
        if user:
            logger.info(f"LOGIN_SUCCESS: {username}")
        else:
            logger.warning(f"LOGIN_FAILED: {username}")
        
        return user
    
    @staticmethod
    def get_user_info(user):
        """
        Lấy thông tin đầy đủ của user.
        
        Returns:
            dict: Thông tin user + profile
        """
        try:
            profile = user.profile
            return {
                'username': user.username,
                'email': user.email,
                'fullname': profile.fullname,
                'phone': profile.phone,
                'date_of_birth': profile.date_of_birth,
                'is_admin': user.is_superuser,
                'is_staff': user.is_staff,
                'created_at': profile.created_at,
            }
        except UserProfile.DoesNotExist:
            return {
                'username': user.username,
                'email': user.email,
                'fullname': '',
                'phone': '',
                'date_of_birth': None,
                'is_admin': user.is_superuser,
                'is_staff': user.is_staff,
                'created_at': user.date_joined,
            }


class InventoryService:
    """Service xử lý inventory operations"""
    
    def __init__(self, engine):
        self.engine = engine
        self.sql_engine = engine.get_sql_engine()
    
    def _get_sql_user_id(self, conn, django_user_id):
        """
        Ánh xạ Django User ID sang SQL Server UserID thông qua Username.
        Đảm bảo tính toàn vẹn Foreign Key mà không cần sync DB cồng kềnh.
        """
        from django.contrib.auth.models import User
        try:
            django_user = User.objects.get(id=django_user_id)
            # 1. Tìm theo Username trong SQL Server
            row = conn.execute(
                text("SELECT UserID FROM dbo.Dim_Users WHERE Username=:u"),
                {"u": django_user.username}
            ).fetchone()
            
            if row:
                return row[0]
            
            # 2. Fallback: Lấy Admin ID đầu tiên nếu không thấy username (đảm bảo FK satisfied)
            fallback = conn.execute(text("SELECT TOP 1 UserID FROM dbo.Dim_Users WHERE Role='Admin' ORDER BY UserID ASC")).fetchone()
            return fallback[0] if fallback else 1 # Mặc định là 1 nếu trắng DB
        except:
            return 1

    def process_outbound(self, item_id, quantity, price, user_id):
        """
        Xuất kho sử dụng stored procedure.
        """
        with self.sql_engine.begin() as conn:
            sql_uid = self._get_sql_user_id(conn, user_id)
            conn.execute(
                text("EXEC sp_SellProduct @ItemID=:id, @QuantityToSell=:qty, @SellingPrice=:price, @UserID=:uid"),
                {"id": int(item_id), "qty": float(quantity), "price": float(price), "uid": sql_uid}
            )
            
            # Get new stock
            result = conn.execute(
                text("SELECT TOP 1 StockQuantity FROM Fact_Inventory_History WHERE ItemID=:id ORDER BY Timestamp DESC"),
                {"id": int(item_id)}
            ).fetchone()
            
            new_stock = result[0] if result else 0
            logger.info(f"OUTBOUND: SKU={item_id}, Qty={quantity}, NewStock={new_stock}, User={sql_uid}")
            return new_stock
    
    def process_inbound(self, item_id, quantity, price, user_id):
        """
        Nhập kho.
        
        Returns:
            float: Stock mới sau khi nhập
        """
        with self.sql_engine.begin() as conn:
            sql_uid = self._get_sql_user_id(conn, user_id)
            # Get current stock
            current = conn.execute(
                text("SELECT TOP 1 StockQuantity FROM Fact_Inventory_History WHERE ItemID=:id ORDER BY Timestamp DESC"),
                {"id": int(item_id)}
            ).fetchone()
            
            current_stock = current[0] if current else 0
            new_stock = current_stock + quantity
            
            # Insert new record
            conn.execute(
                text("INSERT INTO Fact_Inventory_History (ItemID, UserID, Timestamp, Price, OriginalPrice, Discount, StockQuantity, SoldQuantity) "
                     "VALUES (:id, :uid, GETDATE(), :price, :price, 0, :stock, 0)"),
                {"id": int(item_id), "uid": sql_uid, "price": float(price), "stock": new_stock}
            )
            
            logger.info(f"INBOUND: SKU={item_id}, Qty={quantity}, NewStock={new_stock}, User={sql_uid}")
            return new_stock
    
    def add_product(self, item_id, name, category, unit, emission_factor, safety_stock, row, col, user_id):
        """Thêm sản phẩm mới và khởi tạo lịch sử."""
        with self.sql_engine.begin() as conn:
            # 1. Thêm vào bảng Master
            conn.execute(text(
                "INSERT INTO Dim_Products (ItemID, ProductName, Category, Unit, EmissionFactor, SafetyStockLevel, ShelfRow, ShelfColumn, IsActive) "
                "VALUES (:id, :name, :cat, :unit, :ef, :ss, :row, :col, 1)"
            ), {"id": item_id, "name": name, "cat": category, "unit": unit, "ef": float(emission_factor), "ss": float(safety_stock), "row": int(row), "col": int(col)})
            
            # 2. Khởi tạo 6 ngày lịch sử để AI có dữ liệu train
            sql_uid = self._get_sql_user_id(conn, user_id)
            for i in range(5, -1, -1):
                conn.execute(text(
                    "INSERT INTO Fact_Inventory_History (ItemID, UserID, Timestamp, Price, OriginalPrice, Discount, StockQuantity, SoldQuantity) "
                    f"VALUES (:id, :uid, DATEADD(day, -{i}, GETDATE()), 0, 0, 0, 0, 0)"
                ), {"id": item_id, "uid": sql_uid})
            
            return True

    def update_product(self, item_id, name, category, unit, emission_factor, safety_stock, row, col):
        """Cập nhật thông tin sản phẩm."""
        with self.sql_engine.begin() as conn:
            conn.execute(text(
                "UPDATE Dim_Products SET ProductName=:name, Category=:cat, Unit=:unit, "
                "EmissionFactor=:ef, SafetyStockLevel=:ss, ShelfRow=:row, ShelfColumn=:col WHERE ItemID=:id"
            ), {
                "name": name, "cat": category, "unit": unit,
                "ef": float(emission_factor), "ss": float(safety_stock),
                "row": int(row), "col": int(col), "id": item_id
            })
            return True

    def delete_product(self, item_id):
        """Vô hiệu hóa sản phẩm (Soft delete)."""
        with self.sql_engine.begin() as conn:
            conn.execute(text("UPDATE Dim_Products SET IsActive=0 WHERE ItemID=:id"), {"id": item_id})
            return True

    def reload_cache(self):
        """Reset engine cache để load dữ liệu mới"""
        self.engine.load_data()
        logger.info("ENGINE_CACHE_RELOADED")


class ForecastService:
    """Service xử lý forecasting logic"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_forecast_data(self, item_id):
        """
        Lấy dữ liệu dự báo cho 1 SKU.
        
        Returns:
            dict: historical, comparison, future, recommendation
        """
        return {
            'historical': self.engine.get_product_data(item_id),
            'comparison': self.engine.compare_models(item_id),
            'future': self.engine.forecast_future(item_id, days=30),
            'recommendation': self.engine.get_inventory_recommendation(item_id)
        }
    
    def calculate_status(self, current_stock, tomorrow_stock, safety_stock, reorder_point):
        """
        Tính trạng thái tồn kho.
        
        Returns:
            dict: text, color, bg, message
        """
        if tomorrow_stock < safety_stock:
            return {
                'text': 'Nguy cấp (Dưới Safety Stock)',
                'color': 'text-red-400',
                'bg': 'bg-red-500/10 border-red-500/20',
                'message': f'⚠️ CẦN NHẬP HÀNG NGAY! Tồn kho dự báo ({tomorrow_stock:.0f}) < Safety Stock ({safety_stock:.0f}).'
            }
        elif tomorrow_stock < reorder_point:
            return {
                'text': 'Cảnh báo (Sắp đến ROP)',
                'color': 'text-yellow-400',
                'bg': 'bg-yellow-500/10 border-yellow-500/20',
                'message': f'💡 Đề xuất lên đơn PO. Tồn kho dự báo ({tomorrow_stock:.0f}) sắp chạm điểm đặt hàng.'
            }
        else:
            return {
                'text': 'An toàn (Hợp lệ)',
                'color': 'text-green-400',
                'bg': 'bg-green-500/10 border-green-500/20',
                'message': 'Tồn kho ổn định trong vùng an toàn. '
            }


class ChartService:
    """Service xử lý chart rendering"""
    
    @staticmethod
    def build_forecast_chart(hist_data, future_data, safety_stock):
        """
        Build Plotly chart cho forecast.
        
        Returns:
            str: HTML string của chart
        """
        import plotly.graph_objects as go
        import pandas as pd
        
        chart_data = []
        
        # Historical trace
        if not hist_data.empty:
            chart_data.append({
                'x': hist_data["timestamp"].dt.strftime('%Y-%m-%d').tolist(),
                'y': hist_data["stock"].tolist(),
                'name': "Tồn kho thực tế",
                'mode': 'lines+markers',
                'line': {'color': '#3b82f6', 'width': 3},
                'marker': {'size': 6},
                'type': 'scatter'
            })
        
        # Forecast trace
        if len(future_data["forecast_values"]) > 0:
            chart_data.append({
                'x': [pd.Timestamp(d).strftime('%Y-%m-%d') for d in future_data["forecast_dates"]],
                'y': [float(v) for v in future_data["forecast_values"]],
                'name': "Dự báo (AI)",
                'mode': 'lines',
                'line': {'color': '#10b981', 'width': 4, 'shape': 'spline'},
                'fill': 'tozeroy',
                'fillcolor': 'rgba(16, 185, 129, 0.08)',
                'type': 'scatter'
            })
        
        # Safety stock line (invisible trace for legend)
        chart_data.append({
            'x': [None], 
            'y': [None],
            'name': f'Safety Stock ({safety_stock:.0f})',
            'mode': 'lines',
            'line': {'color': '#f59e0b', 'width': 2, 'dash': 'dash'}
        })
        
        # Build figure
        fig = go.Figure(data=chart_data)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            height=600,
            font={'family': "Inter, sans-serif", 'size': 11, 'color': "#cbd5e1"},
            margin={'l': 50, 'r': 20, 't': 20, 'b': 80},
            showlegend=False,
            xaxis={
                'showgrid': True,
                'gridcolor': 'rgba(71, 85, 105, 0.15)',
                'rangeslider': {'visible': True},
            },
            yaxis={
                'showgrid': True,
                'gridcolor': 'rgba(71, 85, 105, 0.15)',
                'rangemode': 'tozero',
            }
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': True, 'responsive': True})
