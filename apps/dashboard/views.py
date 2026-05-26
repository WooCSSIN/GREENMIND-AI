"""
GreenMind Dashboard - Views (Refactored theo chuẩn MVC)
Hệ thống quản lý kho AI - Tối ưu hóa cho Logistics Xanh.
"""

import os
import sys
import logging
import pandas as pd
import plotly.graph_objects as go
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from sqlalchemy import text

# Import Services & Forms
from .services import AuthService, InventoryService, ForecastService, ChartService
from .forms import LoginForm, RegisterForm, TransactionForm

# Import Engine & Controllers
sys.path.append(os.path.abspath(os.path.join(settings.BASE_DIR, 'engine')))
try:
    from greenmind_engine import GreenMindEngine
    from controllers.system_controllers import InventoryController, LogisticsController
except ImportError:
    # Fallback for dev environments
    pass

# Import Utilities
from core.utils.error_sanitizer import sanitize_error
from core.utils.audit import log_audit_action
from core.utils.network import get_client_ip

# Global instances cache for performance
_engine = None
_inventory_ctrl = None
_logistics_ctrl = None
_cache_timestamp = None

def is_technical_admin(user):
    """Xác định user có phải phe kỹ thuật (Technical/DevOps) hay không."""
    return user.is_superuser or user.groups.filter(name='Technical').exists()

def reset_engine_cache():
    """
    Reset global engine cache. Call this after any transaction that modifies inventory.
    This ensures the next page load will fetch fresh data from the database.
    """
    global _engine, _inventory_ctrl, _logistics_ctrl, _cache_timestamp
    _engine = None
    _inventory_ctrl = None
    _logistics_ctrl = None
    _cache_timestamp = None
    logging.info("Engine cache reset - fresh data will be loaded on next request")

def get_engine_instances(force_reload=False):
    """
    Khởi tạo hoặc lấy các instance của AI Engine.
    Fix: Thêm trigger force_reload để reset cache sau khi có giao dịch mới.
    
    Args:
        force_reload (bool): If True, forces a fresh load from database
    
    Returns:
        tuple: (_engine, _inventory_ctrl, _logistics_ctrl)
    """
    global _engine, _inventory_ctrl, _logistics_ctrl, _cache_timestamp
    
    if _engine is None or force_reload:
        _engine = GreenMindEngine()
        _engine.load_data()
        _inventory_ctrl = InventoryController(_engine)
        _logistics_ctrl = LogisticsController(_engine)
        _cache_timestamp = pd.Timestamp.now()
        logging.info(f"Engine cache initialized/reloaded at {_cache_timestamp}")
    
    return _engine, _inventory_ctrl, _logistics_ctrl

# ═══════════════════════════════════════════════════════════
# 1. AUTHENTICATION (REFACTORED)
# ═══════════════════════════════════════════════════════════

def landing_view(request):
    """Trang chủ landing page giới hạn khách vãng lai."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')

def login_view(request):
    """
    Xử lý Đăng nhập & Đăng ký (Refactored).
    Logic nghiệp vụ được đẩy sang AuthService. 
    View chỉ còn nhiệm vụ điều hướng và hiển thị thông báo.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- ACTION: ĐĂNG KÝ ---
        if action == 'register':
            form = RegisterForm(request.POST)
            if form.is_valid():
                user, error = AuthService.register_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    email=form.cleaned_data['email'],
                    fullname=form.cleaned_data['fullname'],
                    phone=form.cleaned_data['phone'],
                    date_of_birth=form.cleaned_data['date_of_birth']
                )
                if error:
                    messages.error(request, f"Lỗi: {error}")
                else:
                    messages.success(request, f"Đăng ký thành công! Chào mừng đại diện doanh nghiệp mới.")
                    return redirect('login')
            else:
                for field, errors in form.errors.items():
                    for error in errors: messages.error(request, error)

        # --- ACTION: ĐĂNG NHẬP ---
        else:
            form = LoginForm(request.POST)
            if form.is_valid():
                user = AuthService.authenticate_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password']
                )
                if user:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, "Xác thực thất bại: Sai tên đăng nhập hoặc mật khẩu.")
            else:
                messages.error(request, "Vui lòng kiểm tra lại thông tin đăng nhập.")
    
    return render(request, 'dashboard/login.html')

def logout_view(request):
    """Xử lý đăng xuất an toàn."""
    logout(request)
    messages.success(request, "Đã ngắt phiên làm việc an toàn.")
    return redirect('login')

# ═══════════════════════════════════════════════════════════
# 2. DASHBOARD & FORECASTING (REFACTORED)
# ═══════════════════════════════════════════════════════════

@login_required(login_url='login')
def home_view(request):
    """
    Trang Dashboard trung tâm - Phân tích & Dự báo AI.
    Sử dụng ForecastService và ChartService để tách biệt logic xử lý dữ liệu.
    """
    try:
        engine, _, _ = get_engine_instances()
        
        # Khởi tạo SKU Mapping
        sku_list = sorted(engine.df['itemid'].dropna().unique())
        sku_names = engine.get_sku_names()
        sku_mapping = {
            f"{str(int(x) if x == int(x) else x)} | {sku_names.get(str(int(x) if x == int(x) else x), 'Sản phẩm không tên')}": x
            for x in sku_list
        }
        
        # Xác định SKU đang được chọn
        input_sku = request.GET.get('sku')
        selected_label = None
        if input_sku:
            for label, sku in sku_mapping.items():
                if str(sku) == str(input_sku):
                    selected_label = label
                    break
        
        if not selected_label:
            # Mặc định lấy SKU có nhiều dữ liệu nhất
            most_active_sku = engine.df['itemid'].value_counts().index[0]
            for label, sku in sku_mapping.items():
                if sku == most_active_sku:
                    selected_label = label
                    break
        
        selected_sku = sku_mapping.get(selected_label)
        selected_name = selected_label.split('|')[1].strip() if '|' in selected_label else selected_label
        
        # Gọi Services xử lý
        forecast_service = ForecastService(engine)
        chart_service = ChartService()
        
        # Lấy dữ liệu dự báo & recommend
        data = forecast_service.get_forecast_data(selected_sku)
        
        # Xây dựng Biểu đồ Plotly
        chart_html = chart_service.build_forecast_chart(
            hist_data=data['historical'],
            future_data=data['future'],
            safety_stock=data['recommendation']['safety_stock_optimized']
        )
        
        # Tính toán trạng thái tồn kho ngày mai
        current_stock = data['historical']["stock"].iloc[-1] if not data['historical'].empty else 0
        tomorrow_demand = float(data['future']["forecast_values"][0]) if len(data['future']["forecast_values"]) > 0 else 0
        tomorrow_stock = max(current_stock - tomorrow_demand, 0)
        
        status = forecast_service.calculate_status(
            current_stock=current_stock,
            tomorrow_stock=tomorrow_stock,
            safety_stock=data['recommendation']['safety_stock_optimized'],
            reorder_point=data['recommendation']['reorder_point']
        )
        
        # Parse Battle Results cho UI
        battle_results = []
        if not data['comparison']['battle_results'].empty:
            for _, row in data['comparison']['battle_results'].iterrows():
                battle_results.append({
                    'Model': row['Model'],
                    'MAE': float(row['MAE']),
                    'RMSE': float(row['RMSE'])
                })
        
        context = {
            'active_page': 'home',
            'sku_mapping': sku_mapping,
            'selected_label': selected_label,
            'selected_sku': selected_sku,
            'selected_name': selected_name,
            'chart_html': chart_html,
            'status': status,
            'tomorrow_stock': tomorrow_stock,
            'results': {
                'champion': data['comparison']['champion'],
                'champion_mae': battle_results[0]['MAE'] if battle_results else 0,
                'maes': battle_results,
                'future_co2_saving': float(data['comparison']['green_impact']['annual_co2_kg']),
                'trees_saving': float(data['comparison']['green_impact']['trees_equivalent']),
            },
            'reco': {
                'safety_stock': float(data['recommendation']['safety_stock_optimized']),
                'reorder_point': float(data['recommendation']['reorder_point']),
                'action_msg': status['message']
            },
            'is_tech_admin': is_technical_admin(request.user)
        }
        return render(request, 'dashboard/home.html', context)
        
    except Exception as e:
        is_tech = is_technical_admin(request.user)
        return render(request, 'dashboard/home.html', {
            'active_page': 'home',
            'error_msg': sanitize_error(e, is_tech),
            'is_tech_admin': is_tech
        })

# ═══════════════════════════════════════════════════════════
# 3. OPERATION VIEWS
# ═══════════════════════════════════════════════════════════

@login_required(login_url='login')
def catalog_view(request):
    """Quản lý danh mục sản phẩm (Master Data)."""
    engine, _, _ = get_engine_instances()
    inventory_service = InventoryService(engine)
    sql_eng = engine.get_sql_engine()

    if request.method == 'POST':
        is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
        if not is_admin:
            messages.error(request, "Quyền hạn không đủ.")
            return redirect('catalog')

        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        
        try:
            if action == 'add':
                inventory_service.add_product(
                    item_id=item_id,
                    name=request.POST.get('name'),
                    category=request.POST.get('category'),
                    unit=request.POST.get('unit'),
                    emission_factor=request.POST.get('emission_factor', 0),
                    safety_stock=request.POST.get('safety_stock', 0),
                    row=request.POST.get('shelf_row', 1),
                    col=request.POST.get('shelf_column', 1),
                    user_id=request.user.id
                )
                messages.success(request, f"Đã thêm SKU mới thành công.")
            
            elif action == 'edit':
                inventory_service.update_product(
                    item_id=item_id,
                    name=request.POST.get('name'),
                    category=request.POST.get('category'),
                    unit=request.POST.get('unit'),
                    emission_factor=request.POST.get('emission_factor', 0),
                    safety_stock=request.POST.get('safety_stock', 0),
                    row=request.POST.get('shelf_row', 1),
                    col=request.POST.get('shelf_column', 1)
                )
                messages.success(request, f"Cập nhật thành công SKU: {item_id}")
            
            elif action == 'delete':
                inventory_service.delete_product(item_id)
                messages.success(request, f"Đã vô hiệu hóa SKU: {item_id}")

            # Reset cache để dashboard cập nhật ngay lập tức
            reset_engine_cache()
            logging.info(f"Catalog action '{action}' completed for SKU={item_id} by {request.user.username}")
            
        except Exception as e:
            messages.error(request, sanitize_error(e, is_technical_admin(request.user)))
            logging.error(f"Catalog action failed: {str(e)}", exc_info=True)

    try:
        df_prod = pd.read_sql("SELECT * FROM Dim_Products WHERE IsActive=1 ORDER BY ItemID DESC", con=sql_eng)
        products = df_prod.to_dict('records')
    except:
        products = []
        
    return render(request, 'dashboard/catalog.html', {
        'active_page': 'catalog', 'products': products,
        'is_admin': request.user.is_superuser or request.user.groups.filter(name='Admin').exists(),
        'is_tech_admin': is_technical_admin(request.user)
    })

@login_required(login_url='login')
def simulator_view(request):
    """Mô phỏng nhập xuất kho (Refactored)."""
    engine, _, _ = get_engine_instances()
    inventory_service = InventoryService(engine)
    
    sku_list = sorted(engine.df['itemid'].dropna().unique())
    sku_names = engine.get_sku_names()
    sku_mapping = { f"{str(int(x) if x == int(x) else x)} | {sku_names.get(str(int(x) if x == int(x) else x), 'SKU ' + str(x))}": x for x in sku_list }
    
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    transaction_success = False
    new_stock_level = 0
    
    if request.method == 'POST':
        if not is_admin:
            messages.error(request, "Quyền hạn không đủ.")
            return redirect('simulator')
        
        sim_sku_val = sku_mapping.get(request.POST.get('sku'))
        sim_type = request.POST.get('type')
        sim_qty = float(request.POST.get('qty', 0))
        sim_price = float(request.POST.get('price', 0))
        
        try:
            if sim_type == 'outbound':
                new_stock_level = inventory_service.process_outbound(sim_sku_val, sim_qty, sim_price, request.user.id)
            else:
                new_stock_level = inventory_service.process_inbound(sim_sku_val, sim_qty, sim_price, request.user.id)

            # 1. Reset in-process engine cache
            reset_engine_cache()

            # 2. Broadcast transaction immediately via WebSocket
            from .tasks import broadcast_transaction, run_forecast_async
            broadcast_transaction(
                sku=sim_sku_val,
                transaction_type=sim_type,
                quantity=sim_qty,
                new_stock=new_stock_level,
                performed_by=request.user.username,
            )

            # 3. Trigger async forecast update (non-blocking)
            run_forecast_async.delay(str(sim_sku_val))

            transaction_success = True
            messages.success(request, f"Giao dịch thành công! Tồn kho mới: {new_stock_level}")
            logging.info(f"Transaction: {sim_type} SKU={sim_sku_val} Qty={sim_qty} by {request.user.username}")

        except Exception as e:
            messages.error(request, sanitize_error(e, is_technical_admin(request.user)))
            logging.error(f"Transaction failed: {str(e)}", exc_info=True)
    
    return render(request, 'dashboard/simulator.html', {
        'active_page': 'simulator', 'sku_mapping': sku_mapping,
        'is_admin': is_admin, 'transaction_success': transaction_success,
        'new_stock_level': new_stock_level, 'is_tech_admin': is_technical_admin(request.user)
    })

@login_required(login_url='login')
def monitoring_view(request):
    """Giám sát sức khỏe hệ thống & Bản đồ kho."""
    engine, _, _ = get_engine_instances()
    try:
        sql_eng = engine.get_sql_engine()
        history = pd.read_sql("SELECT TOP 30 * FROM Fact_Inventory_History ORDER BY Timestamp DESC", con=sql_eng).to_dict('records')
        audit_logs = pd.read_sql("SELECT TOP 30 a.*, u.Username FROM Admin_Action_Logs a LEFT JOIN Dim_Users u ON a.UserID = u.UserID ORDER BY Timestamp DESC", con=sql_eng).to_dict('records')
        warnings = pd.read_sql("SELECT * FROM Inventory_CO2_Warnings ORDER BY WarningTime DESC", con=sql_eng).to_dict('records')
        
        query_map = """
            SELECT p.ShelfRow, p.ShelfColumn, p.ProductName, ISNULL(f.StockQuantity, 0) as StockQuantity
            FROM Dim_Products p
            LEFT JOIN (SELECT ItemID, StockQuantity, ROW_NUMBER() OVER (PARTITION BY ItemID ORDER BY Timestamp DESC) as rn FROM Fact_Inventory_History) f 
            ON p.ItemID = f.ItemID AND f.rn = 1 WHERE p.IsActive = 1
        """
        map_df = pd.read_sql(query_map, con=sql_eng)
        
        # Heatmap calculation
        # ... logic as before but concise
        total_stock = map_df['StockQuantity'].sum()
        
        return render(request, 'dashboard/monitoring.html', {
            'active_page': 'monitoring', 'history': history, 'audit_logs': audit_logs, 
            'warnings': warnings, 'heatmap_items': map_df.to_dict('records'),
            'total_stock': total_stock, 'fill_rate': (map_df['StockQuantity'] > 0).mean() * 100 if not map_df.empty else 0,
            'is_tech_admin': is_technical_admin(request.user)
        })
    except Exception as e:
        messages.error(request, f"Lỗi Monitoring: {str(e)}")
        return redirect('home')

@login_required(login_url='login')
def esg_view(request):
    """Báo cáo tác động môi trường."""
    engine, _, _ = get_engine_instances()
    try:
        esg_data = engine.get_esg_metrics()
        chart_df = esg_data["trend_df"]
        fig = go.Figure([
            go.Bar(x=chart_df["Thứ tự"], y=chart_df["Phát thải cơ sở (Gồm lãng phí)"], name="Baseline", marker_color="#475569"),
            go.Bar(x=chart_df["Thứ tự"], y=chart_df["Phát thải AI (Optimized)"], name="AI Optimized", marker_color="#10b981")
        ])
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
        
        return render(request, 'dashboard/esg.html', {
            'active_page': 'esg', 'esg_data': esg_data, 
            'esg_chart_html': fig.to_html(full_html=False, include_plotlyjs='cdn'),
            'is_tech_admin': is_technical_admin(request.user)
        })
    except Exception as e:
        messages.error(request, f"Lỗi ESG: {str(e)}")
        return redirect('home')

@login_required(login_url='login')
def health_check_view(request):
    """Dành riêng cho DevOps/Admin Kỹ thuật."""
    if not is_technical_admin(request.user):
        messages.error(request, "Quyền truy cập bị từ chối.")
        return redirect('home')
    
    if request.method == 'POST':
        from scripts import health_check
        res = health_check.run_health_check(triggered_by=request.user.username)
        messages.success(request, "Health check hoàn tất.")
        request.session['hc_results'] = res
        return redirect('health_check')
        
    return render(request, 'dashboard/health_check.html', {
        'active_page': 'health_check', 'is_tech_admin': True,
        'hc_results': request.session.pop('hc_results', None)
    })

# Error Handlers
def error_404_view(request, exception): return render(request, '404.html', status=404)
def error_500_view(request): return render(request, '500.html', status=500)
