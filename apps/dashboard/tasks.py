"""
GreenMind Dashboard - Celery Tasks
Async ML tasks to avoid blocking the web request.
"""

import json
import logging
from datetime import datetime
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger("celery")
channel_layer = get_channel_layer()

GROUP_DASHBOARD = "dashboard_updates"
GROUP_ALERTS    = "inventory_alerts"


# ─────────────────────────────────────────────────────────────────────────────
# BROADCAST HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _broadcast(group: str, event: dict):
    """Send event to a channel group (sync wrapper)."""
    try:
        async_to_sync(channel_layer.group_send)(group, event)
    except Exception as e:
        logger.error(f"[Celery] Broadcast failed: {e}")


def broadcast_transaction(sku, transaction_type, quantity, new_stock, performed_by=""):
    """Broadcast a transaction event to all dashboard users."""
    ts = datetime.now().isoformat()
    _broadcast(GROUP_DASHBOARD, {
        "type": "chart_update",
        "sku": str(sku),
        "stock": float(new_stock),
        "transaction_type": transaction_type,
        "quantity": float(quantity),
        "timestamp": ts,
    })
    _broadcast(GROUP_DASHBOARD, {
        "type": "transaction_notify",
        "sku": str(sku),
        "transaction_type": transaction_type,
        "quantity": float(quantity),
        "new_stock": float(new_stock),
        "performed_by": performed_by,
        "timestamp": ts,
    })
    # Also broadcast to SKU-specific group
    _broadcast(f"sku_{sku}", {
        "type": "chart_update",
        "sku": str(sku),
        "stock": float(new_stock),
        "transaction_type": transaction_type,
        "quantity": float(quantity),
        "timestamp": ts,
    })


def broadcast_inventory_alert(sku, current_stock, safety_stock):
    """Broadcast inventory alert when stock is low."""
    ts = datetime.now().isoformat()

    if current_stock < safety_stock:
        level   = "critical"
        message = f"⚠️ NGUY CẤP: SKU {sku} dưới mức Safety Stock! ({current_stock:.0f} < {safety_stock:.0f})"
    elif current_stock < safety_stock * 1.5:
        level   = "warning"
        message = f"⚡ CẢNH BÁO: SKU {sku} sắp chạm Safety Stock ({current_stock:.0f})"
    else:
        return  # No alert needed

    _broadcast(GROUP_ALERTS, {
        "type": "inventory_alert",
        "alert_level": level,
        "message": message,
        "sku": str(sku),
        "current_stock": float(current_stock),
        "safety_stock": float(safety_stock),
        "timestamp": ts,
    })
    logger.info(f"[Alert] {level.upper()} for SKU {sku}: stock={current_stock}, safety={safety_stock}")


# ─────────────────────────────────────────────────────────────────────────────
# CELERY TASKS
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def run_forecast_async(self, item_id: str):
    """
    Run AI forecast for a SKU asynchronously.
    Called after a transaction to update predictions in background.
    Results are broadcast via WebSocket when ready.
    """
    try:
        import sys, os
        from django.conf import settings
        sys.path.insert(0, os.path.join(settings.BASE_DIR, "engine"))
        from greenmind_engine import GreenMindEngine

        logger.info(f"[Task] Starting forecast for SKU {item_id}")

        engine = GreenMindEngine()
        engine.load_data()

        # Run forecast
        comparison   = engine.compare_models(item_id)
        future       = engine.forecast_future(item_id, days=30)
        reco         = engine.get_inventory_recommendation(item_id)

        # Get latest stock
        product_data = engine.get_product_data(item_id)
        current_stock = float(product_data["stock"].iloc[-1]) if not product_data.empty else 0
        safety_stock  = float(reco["safety_stock_optimized"])

        # Broadcast updated chart data
        ts = datetime.now().isoformat()
        _broadcast(GROUP_DASHBOARD, {
            "type": "chart_update",
            "sku": str(item_id),
            "stock": current_stock,
            "transaction_type": "forecast_update",
            "quantity": 0,
            "timestamp": ts,
        })

        # Check and broadcast alert
        broadcast_inventory_alert(item_id, current_stock, safety_stock)

        logger.info(f"[Task] Forecast complete for SKU {item_id} | Champion: {comparison['champion']}")
        return {
            "sku": str(item_id),
            "champion": comparison["champion"],
            "safety_stock": safety_stock,
            "status": "success",
        }

    except Exception as exc:
        logger.error(f"[Task] Forecast failed for SKU {item_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def check_all_inventory_alerts(self):
    """
    Scheduled task: Check all SKUs for low stock alerts.
    Runs every 15 minutes via Celery Beat.
    """
    try:
        import sys, os
        from django.conf import settings
        sys.path.insert(0, os.path.join(settings.BASE_DIR, "engine"))
        from greenmind_engine import GreenMindEngine

        engine = GreenMindEngine()
        engine.load_data()

        if engine.df is None or engine.df.empty:
            return {"status": "no_data"}

        sku_list = engine.df["itemid"].unique()
        alerts_sent = 0

        for sku in sku_list:
            try:
                product_data = engine.get_product_data(sku)
                if product_data.empty:
                    continue

                reco          = engine.get_inventory_recommendation(sku)
                current_stock = float(product_data["stock"].iloc[-1])
                safety_stock  = float(reco["safety_stock_optimized"])

                broadcast_inventory_alert(sku, current_stock, safety_stock)
                alerts_sent += 1
            except Exception as e:
                logger.warning(f"[Task] Alert check failed for SKU {sku}: {e}")
                continue

        logger.info(f"[Task] Inventory alert check complete. Processed {alerts_sent} SKUs.")
        return {"status": "success", "skus_checked": alerts_sent}

    except Exception as exc:
        logger.error(f"[Task] check_all_inventory_alerts failed: {exc}")
        raise


@shared_task(bind=True)
def refresh_heatmap(self):
    """
    Scheduled task: Refresh warehouse heatmap data.
    Runs every 5 minutes via Celery Beat.
    """
    try:
        import sys, os, pandas as pd
        from django.conf import settings
        from sqlalchemy import create_engine as sa_create_engine
        sys.path.insert(0, os.path.join(settings.BASE_DIR, "engine"))
        from greenmind_engine import GreenMindEngine

        engine = GreenMindEngine()
        sql_eng = engine.get_sql_engine()

        query = """
            SELECT p.ShelfRow, p.ShelfColumn, p.ProductName,
                   ISNULL(f.StockQuantity, 0) as StockQuantity
            FROM Dim_Products p
            LEFT JOIN (
                SELECT ItemID, StockQuantity,
                       ROW_NUMBER() OVER (PARTITION BY ItemID ORDER BY Timestamp DESC) as rn
                FROM Fact_Inventory_History
            ) f ON p.ItemID = f.ItemID AND f.rn = 1
            WHERE p.IsActive = 1
        """
        map_df = pd.read_sql(query, con=sql_eng)
        items  = map_df.to_dict("records")

        _broadcast(GROUP_DASHBOARD, {
            "type": "heatmap_update",
            "items": items,
            "timestamp": datetime.now().isoformat(),
        })

        logger.info(f"[Task] Heatmap refreshed with {len(items)} items")
        return {"status": "success", "items": len(items)}

    except Exception as exc:
        logger.error(f"[Task] refresh_heatmap failed: {exc}")
        raise
