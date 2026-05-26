"""
GreenMind AI - Health Check Script
===================================
Chạy script này để xác nhận CSDL SQL Server và các thiết lập biến an toàn,
trước khi khởi động hệ thống Django hoặc chạy từ trang Quản trị.
"""

import os
import sys
import traceback
from sqlalchemy import text
from dotenv import load_dotenv

# Nạp biến môi trường từ .env (ở thư mục gốc)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

def log_health_check(engine, status, details, triggered_by='system'):
    """Ghi log Health Check vào CSDL (bảng System_Health_Log)"""
    try:
        sql_eng = engine.get_sql_engine()
        with sql_eng.begin() as conn:
            # Đảm bảo bảng này luôn tồn tại trước khi Insert (Idempotent)
            conn.execute(text('''
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'System_Health_Log')
                BEGIN
                    CREATE TABLE System_Health_Log (
                        LogID INT IDENTITY(1, 1) PRIMARY KEY,
                        CheckTime DATETIME DEFAULT GETDATE(),
                        Status NVARCHAR(20) NOT NULL,
                        Details NVARCHAR(MAX),
                        TriggeredBy NVARCHAR(100) DEFAULT 'system'
                    );
                END
            '''))
            
            conn.execute(text(
                "INSERT INTO System_Health_Log (Status, Details, TriggeredBy) "
                "VALUES (:status, :details, :trigger)"
            ), {"status": status, "details": details, "trigger": triggered_by})
            
            log_id = conn.execute(text("SELECT TOP 1 LogID FROM System_Health_Log ORDER BY LogID DESC")).scalar()
            return log_id
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"⚠️ Không thể ghi log vào CSDL: Chi tiết lỗi = {e}")
        return None

def run_health_check(triggered_by='system'):
    """Chaỵ toàn bộ quy trình kiểm tra và trả về kết quả dạng dictionary."""
    results = {
        "status": "OK",
        "env_vars": {"status": "OK", "details": []},
        "database": {"status": "OK", "details": []},
        "ai_pipeline": {"status": "OK", "details": []},
        "summary": "",
        "log_id": None
    }
    
    details_str = []
    
    # 1. Kiểm tra biến môi trường
    required_vars = ["DB_SERVER", "DB_NAME", "SECRET_KEY", "STORAGE_KWH_PER_UNIT"]
    missing = []
    for var in required_vars:
        val = os.getenv(var)
        if not val:
            missing.append(var)
            results["env_vars"]["details"].append(f"❌ {var}: Không tìm thấy")
        else:
            if var == "SECRET_KEY":
                val = val[:5] + "***"
            results["env_vars"]["details"].append(f"✅ {var}: Định cấu hình ({val})")
            
    if missing:
        results["env_vars"]["status"] = "FAIL"
        results["status"] = "FAIL"
        details_str.append(f"Thiếu biến môi trường: {', '.join(missing)}")
    else:
        details_str.append("Kiểm tra biến môi trường: OK")

    # 2. Kiểm tra Database & AI
    engine = None
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine'))
        from greenmind_engine import GreenMindEngine
        engine = GreenMindEngine()
        sql_eng = engine.get_sql_engine()
        with sql_eng.connect() as conn:
            results["database"]["details"].append(f"✅ Đã kết nối thành công tới {engine.server}\\{engine.database}")
            
            # Kiểm tra bảng
            required_tables = ["Dim_Products", "Fact_Inventory_History", "Dim_Users", "Fact_AI_Predictions", "Green_Impact_Logs"]
            tables_checked = 0
            for table in required_tables:
                rs = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                results["database"]["details"].append(f"✅ Bảng {table}: Có sẵn ({rs} bản ghi)")
                tables_checked += 1
                
            # Kiểm tra cột IsActive
            has_isactive = conn.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'Dim_Products' AND COLUMN_NAME = 'IsActive'"
            )).scalar()
            if has_isactive > 0:
                results["database"]["details"].append("✅ Cột Dim_Products.IsActive: Đã tạo")
            else:
                results["database"]["details"].append("❌ Cột Dim_Products.IsActive: Mất tích")
                results["database"]["status"] = "FAIL"
                
            # Kiểm tra cột UserID
            has_userid = conn.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'Fact_Inventory_History' AND COLUMN_NAME = 'UserID'"
            )).scalar()
            if has_userid > 0:
                results["database"]["details"].append("✅ Cột Fact_Inventory_History.UserID: Đã tạo")
            else:
                results["database"]["details"].append("❌ Cột Fact_Inventory_History.UserID: Mất tích")
                results["database"]["status"] = "FAIL"
                
            details_str.append(f"Đã kiểm tra {tables_checked} bảng hệ thống.")
            
    except Exception as e:
        results["database"]["status"] = "FAIL"
        results["status"] = "FAIL"
        err_msg = f"Lỗi kết nối CSDL: {str(e)}"
        results["database"]["details"].append(f"❌ {err_msg}")
        details_str.append(err_msg)

    # 3. Chạy thử AI Pipeline 
    if engine and results["database"]["status"] == "OK":
        try:
            df = engine.load_data()
            results["ai_pipeline"]["details"].append(f"✅ Data Loader: Tải thành công {len(df) if df is not None else 0} dòng tồn kho.")
            
            if df is not None and not df.empty:
                sku_names = engine.get_sku_names()
                valid_skus = df.groupby('itemid').filter(lambda x: len(x) > 10)['itemid'].unique()
                if len(valid_skus) > 0:
                    sample_sku = str(int(valid_skus[0]))
                    results["ai_pipeline"]["details"].append(f"✅ AI Pipeline: Đang test SKU: {sample_sku}")
                    
                    # Chạy Compare
                    res_cmp = engine.compare_models(sample_sku)
                    champion = res_cmp["champion"]
                    results["ai_pipeline"]["details"].append(f"✅ So khớp Model: Hoàn tất (Champion = {champion})")
                    details_str.append(f"AI Pipeline test OK (Champion: {champion})")
                else:
                    results["ai_pipeline"]["details"].append("⚠️ AI Pipeline: Không có SKU nào đủ 10 dòng để test sâu.")
                    details_str.append("AI Pipeline test: Bỏ qua (thiếu dữ liệu)")
            else:
                results["ai_pipeline"]["details"].append("⚠️ AI Pipeline: Dữ liệu trống.")
                details_str.append("AI Pipeline test: Bỏ qua (dữ liệu trống)")
                
        except Exception as e:
            results["ai_pipeline"]["status"] = "FAIL"
            results["status"] = "FAIL"
            err_msg = f"Lỗi AI Pipeline: {str(e)}"
            results["ai_pipeline"]["details"].append(f"❌ {err_msg}")
            details_str.append(err_msg)
            
    if results["database"]["status"] == "FAIL":
        results["status"] = "FAIL"
        
    results["summary"] = " | ".join(details_str)
    
    # Ghi log vào DB nếu có thể
    if engine:
        log_id = log_health_check(engine, results["status"], "\n".join(details_str), triggered_by)
        if log_id:
            results["log_id"] = log_id
            
    return results

def main():
    print("BẮT ĐẦU KIỂM TRA HỆ THỐNG GREENMIND AI\n")
    res = run_health_check('cli')
    
    print("\n--- 1. Biến môi trường ---")
    print("\n".join(res["env_vars"]["details"]))
    
    print("\n--- 2. Database ---")
    print("\n".join(res["database"]["details"]))
    
    print("\n--- 3. AI Pipeline ---")
    print("\n".join(res["ai_pipeline"]["details"]))
    
    print(f"\nSTATUS: {res['status']}")
    if res.get("log_id"):
        print(f"Đã ghi log vào CSDL (LogID: {res['log_id']})")
        
    if res["status"] == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
