"""
GreenMind E2E Automated Worker
================================
Script chạy tự động hàng đêm để:
  1. Tải lại dữ liệu mới nhất từ SQL Server.
  2. Chạy "Battle of Models" cho toàn bộ SKU.
  3. Đồng bộ Safety Stock tối ưu từ AI về SQL Server (Feedback Loop).
  4. Ghi Predictions vào bảng Fact_AI_Predictions.
  5. In báo cáo tóm tắt.

Cách chạy thủ công:
  python worker.py

Cách lên lịch tự động (Windows Task Scheduler):
  - Program: D:\\GREENMIND\\venv\\bin\\python.exe
  - Arguments: D:\\GREENMIND\\worker.py
  - Trigger: Hàng ngày lúc 02:00 AM

Cách lên lịch (Linux Crontab):
  0 2 * * * /path/to/venv/bin/python /path/to/GREENMIND/worker.py >> /var/log/greenmind_worker.log 2>&1
"""

import sys
import os
import logging
from datetime import datetime

# ─── Setup path để import engine ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "engine"))

# ─── Load .env ────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass  # dotenv không bắt buộc khi biến đã được set ở OS level

# ─── Cấu hình Logging ─────────────────────────────────────────────────────────
LOG_DIR = os.path.join(BASE_DIR, "outputs", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"worker_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("greenmind.worker")


def run_e2e_pipeline():
    """Hàm chính: Thực thi toàn bộ pipeline E2E."""
    logger.info("=" * 60)
    logger.info("  GREENMIND E2E WORKER - BẮT ĐẦU")
    logger.info(f"  Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ── BƯỚC 1: Khởi tạo Engine ─────────────────────────────────────────────
    logger.info("[BƯỚC 1/4] Khởi tạo GreenMind Engine và kết nối SQL Server...")
    try:
        from greenmind_engine import GreenMindEngine
        from controllers.system_controllers import InventoryController

        DB_SERVER = os.getenv("DB_SERVER", r"DESKTOP-65L3CQO\KMS")
        DB_NAME = os.getenv("DB_NAME", "GRW")

        engine = GreenMindEngine(server=DB_SERVER, database=DB_NAME)
        engine.load_data()
        ctrl = InventoryController(engine)
        logger.info(f"  ✅ Kết nối thành công! Tổng bản ghi: {len(engine.df):,}")
    except Exception as e:
        logger.critical(f"  ❌ Không thể khởi tạo Engine: {e}")
        return False

    # ── BƯỚC 2: Lấy danh sách SKU ───────────────────────────────────────────
    logger.info("[BƯỚC 2/4] Lấy danh sách SKU đang hoạt động...")
    sku_list = engine.df["itemid"].unique().tolist()
    logger.info(f"  📦 Tổng số SKU cần xử lý: {len(sku_list)}")

    # ── BƯỚC 3: Chạy Model Battle + Feedback Loop ───────────────────────────
    logger.info("[BƯỚC 3/4] Chạy Model Battle & Đồng bộ Safety Stock...")
    results_summary = []
    errors = []

    for i, sku in enumerate(sku_list, 1):
        try:
            logger.info(f"  [{i}/{len(sku_list)}] Đang xử lý SKU: {sku:.0f}...")

            # Chạy Model Battle
            compare_res = engine.compare_models(sku)
            champion = compare_res["champion"]
            mae = compare_res["battle_results"].iloc[0]["MAE"]
            co2_saving = compare_res["green_impact"]["annual_co2_kg"]

            # Feedback Loop: Ghi Safety Stock tối ưu về DB
            new_ss = engine.sync_safety_stock_to_db(sku)

            # Ghi kết quả dự báo vào Fact_AI_Predictions
            _save_prediction_to_db(engine, sku, champion, mae)

            results_summary.append({
                "sku": sku,
                "champion": champion,
                "mae": round(mae, 4),
                "new_safety_stock": round(new_ss, 2),
                "co2_saving_annual_kg": round(co2_saving, 2),
            })
            logger.info(f"    ✅ Champion: {champion} | MAE: {mae:.2f} | SS mới: {new_ss:.1f} | CO2 tiết kiệm: {co2_saving:.1f} kg/năm")

        except Exception as e:
            logger.warning(f"    ⚠️  SKU {sku} thất bại: {e}")
            errors.append({"sku": sku, "error": str(e)})

    # ── BƯỚC 4: Tóm tắt & Báo cáo ───────────────────────────────────────────
    logger.info("[BƯỚC 4/4] Tổng kết...")
    total_co2 = sum(r["co2_saving_annual_kg"] for r in results_summary)
    total_trees = total_co2 / 20
    champion_counts = {}
    for r in results_summary:
        champion_counts[r["champion"]] = champion_counts.get(r["champion"], 0) + 1

    logger.info("=" * 60)
    logger.info("  📊 BÁO CÁO KẾT QUẢ E2E WORKER")
    logger.info(f"  ✅ Thành công : {len(results_summary)}/{len(sku_list)} SKU")
    logger.info(f"  ❌ Thất bại  : {len(errors)} SKU")
    logger.info(f"  🤖 Model wins: {champion_counts}")
    logger.info(f"  🌿 Tiềm năng tiết kiệm: {total_co2:.1f} kg CO2/năm ≈ {total_trees:.1f} cây xanh")
    logger.info("=" * 60)

    return True


def _save_prediction_to_db(engine, sku, champion, mae):
    """Ghi kết quả dự báo vào bảng Fact_AI_Predictions."""
    try:
        from sqlalchemy import text
        sql_eng = engine.get_sql_engine()
        future = engine.forecast_future(sku, days=7)
        next_7_day_avg = float(sum(future["forecast_values"][:7]) / min(7, len(future["forecast_values"])))

        with sql_eng.begin() as conn:
            # Kiểm tra nếu bảng tồn tại
            check = conn.execute(
                text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Fact_AI_Predictions'")
            ).scalar()
            if check:
                conn.execute(
                    text("""
                        INSERT INTO Fact_AI_Predictions 
                            (ItemID, ModelUsed, MAE, PredictedStockNext7DayAvg, RunTimestamp)
                        VALUES 
                            (:id, :model, :mae, :pred, GETDATE())
                    """),
                    {"id": int(sku), "model": champion, "mae": mae, "pred": next_7_day_avg},
                )
    except Exception as e:
        logger.warning(f"    [DB] Không thể ghi Fact_AI_Predictions cho SKU {sku}: {e}")


if __name__ == "__main__":
    success = run_e2e_pipeline()
    exit_code = 0 if success else 1
    logger.info(f"Worker kết thúc với exit code: {exit_code}")
    sys.exit(exit_code)
