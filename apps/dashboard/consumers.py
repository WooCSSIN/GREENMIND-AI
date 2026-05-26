"""
GreenMind Dashboard - WebSocket Consumers
Real-time updates for dashboard, alerts, and heatmap.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

logger = logging.getLogger("channels")

# Group names
GROUP_DASHBOARD = "dashboard_updates"
GROUP_ALERTS    = "inventory_alerts"


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates.

    Events pushed to client:
    - chart_update        : New forecast / stock data
    - inventory_alert     : Stock below safety level
    - heatmap_update      : Warehouse heatmap changed
    - transaction_notify  : A transaction was recorded
    """

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.user_group = f"user_{self.user_id}"

        # Reject unauthenticated connections
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        # Join global dashboard group + personal group
        await self.channel_layer.group_add(GROUP_DASHBOARD, self.channel_name)
        await self.channel_layer.group_add(GROUP_ALERTS,    self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()
        logger.info(f"[WS] User {self.user_id} connected")

        # Send welcome message with current status
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Kết nối real-time thành công",
            "user_id": self.user_id,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GROUP_DASHBOARD, self.channel_name)
        await self.channel_layer.group_discard(GROUP_ALERTS,    self.channel_name)
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        logger.info(f"[WS] User {self.user_id} disconnected (code={close_code})")

    async def receive(self, text_data):
        """Handle messages from client."""
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "subscribe_sku":
                await self._subscribe_sku(data.get("sku"))
            elif msg_type == "unsubscribe_sku":
                await self._unsubscribe_sku(data.get("sku"))
            elif msg_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[WS] Bad message from user {self.user_id}: {e}")

    # ─── Event Handlers (called via channel_layer.group_send) ─────────────────

    async def chart_update(self, event):
        """Push new chart/forecast data to client."""
        await self.send(text_data=json.dumps({
            "type": "chart_update",
            "sku": event["sku"],
            "stock": event["stock"],
            "transaction_type": event.get("transaction_type", ""),
            "quantity": event.get("quantity", 0),
            "timestamp": event["timestamp"],
        }))

    async def inventory_alert(self, event):
        """Push inventory alert to client."""
        await self.send(text_data=json.dumps({
            "type": "inventory_alert",
            "alert_level": event["alert_level"],   # 'critical' | 'warning' | 'info'
            "message": event["message"],
            "sku": event["sku"],
            "current_stock": event.get("current_stock", 0),
            "safety_stock": event.get("safety_stock", 0),
            "timestamp": event["timestamp"],
        }))

    async def heatmap_update(self, event):
        """Push warehouse heatmap update to client."""
        await self.send(text_data=json.dumps({
            "type": "heatmap_update",
            "items": event["items"],
            "timestamp": event["timestamp"],
        }))

    async def transaction_notify(self, event):
        """Push transaction notification to client."""
        await self.send(text_data=json.dumps({
            "type": "transaction_notify",
            "sku": event["sku"],
            "transaction_type": event["transaction_type"],
            "quantity": event["quantity"],
            "new_stock": event["new_stock"],
            "performed_by": event.get("performed_by", ""),
            "timestamp": event["timestamp"],
        }))

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _subscribe_sku(self, sku):
        if not sku:
            return
        group = f"sku_{sku}"
        await self.channel_layer.group_add(group, self.channel_name)
        await self.send(text_data=json.dumps({
            "type": "subscribed",
            "sku": sku,
        }))
        logger.debug(f"[WS] User {self.user_id} subscribed to SKU {sku}")

    async def _unsubscribe_sku(self, sku):
        if not sku:
            return
        group = f"sku_{sku}"
        await self.channel_layer.group_discard(group, self.channel_name)
        logger.debug(f"[WS] User {self.user_id} unsubscribed from SKU {sku}")
