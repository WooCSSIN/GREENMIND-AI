# 🚀 Real-Time Implementation Guide for GreenMind AI

**Status:** Implementation Plan  
**Technology:** Django Channels + Redis + Plotly  
**Estimated Effort:** 8-12 hours  
**Complexity:** Medium

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Real-Time Use Cases](#real-time-use-cases)
3. [Technology Stack](#technology-stack)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Code Examples](#code-examples)
6. [Testing & Deployment](#testing--deployment)
7. [Performance Optimization](#performance-optimization)

---

## 🏗️ Architecture Overview

### Current Architecture (Polling-Based)
```
User → Browser → Django View → Database
                    ↓
                 Response (HTML/JSON)
                    ↓
                 Browser renders
                 
Problem: User must refresh page to see updates
```

### New Architecture (Real-Time with Channels)
```
User 1 → Browser 1 ─┐
                     ├─→ WebSocket ─→ Django Channels ─→ Redis Pub/Sub
User 2 → Browser 2 ─┤                                        ↓
User 3 → Browser 3 ─┘                                   Database
                                                            ↓
                                                    Event triggered
                                                            ↓
                                                    Broadcast to all
                                                    connected clients
                                                            ↓
                                                    Browsers update
                                                    in real-time
```

### Component Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Dashboard (Plotly Chart, Heatmap, Alerts)           │   │
│  │ WebSocket Connection: ws://localhost:8000/ws/...    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↕ WebSocket
┌─────────────────────────────────────────────────────────────┐
│              Django Channels (ASGI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ WebSocket Consumer (DashboardConsumer)              │   │
│  │ - connect()                                          │   │
│  │ - disconnect()                                       │   │
│  │ - receive()                                          │   │
│  │ - chart_update()                                     │   │
│  │ - alert_notification()                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↕ Pub/Sub
┌─────────────────────────────────────────────────────────────┐
│                    Redis (Message Broker)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Channels:                                            │   │
│  │ - dashboard_updates                                  │   │
│  │ - inventory_alerts                                   │   │
│  │ - forecast_updates                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↕ Events
┌─────────────────────────────────────────────────────────────┐
│                   Django Backend (WSGI)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Views (simulator_view, catalog_view)                │   │
│  │ Services (InventoryService, ForecastService)        │   │
│  │ Signals (post_save, post_delete)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↕ ORM
┌─────────────────────────────────────────────────────────────┐
│                   SQL Server Database                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Dim_Products, Fact_Inventory_History, etc.          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Real-Time Use Cases

### Use Case 1: Dashboard Chart Update
```
Timeline:
1. User A performs inbound transaction (add 100 units)
2. Backend updates database
3. AI engine recalculates forecast
4. Event published to Redis: "forecast_updated"
5. All connected users receive new chart data
6. Charts update in real-time (no page refresh)
```

### Use Case 2: Inventory Alert
```
Timeline:
1. Stock level drops below safety stock
2. Alert triggered
3. Event published: "inventory_alert"
4. All users see red alert banner
5. Mobile app receives push notification
```

### Use Case 3: Heatmap Update
```
Timeline:
1. Warehouse heatmap shows real-time stock levels
2. When transaction occurs, heatmap updates
3. Color changes reflect new stock levels
4. No page refresh needed
```

### Use Case 4: Multi-User Collaboration
```
Timeline:
1. User A viewing dashboard
2. User B performs transaction
3. User A's dashboard updates automatically
4. Both see same data in real-time
```

---

## 🛠️ Technology Stack

### Backend
- **Django Channels** - WebSocket support for Django
- **Redis** - Message broker & Pub/Sub
- **Celery** (optional) - Async task processing for heavy ML jobs

### Frontend
- **Plotly.js** - Real-time chart updates
- **JavaScript WebSocket API** - Client-side connection
- **Bootstrap/Tailwind** - UI notifications

### Infrastructure
- **Redis Server** - Message broker
- **Daphne** - ASGI server (replaces Gunicorn for WebSocket)

---

## 📝 Step-by-Step Implementation

### Step 1: Install Dependencies

```bash
pip install channels channels-redis daphne
```

**requirements.txt:**
```
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
redis==5.0.0
```

---

### Step 2: Configure Django Settings

**core/settings.py:**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'daphne',  # Must be first
    'channels',
    'apps.dashboard',
    'apps.api',
]

# ASGI Application
ASGI_APPLICATION = 'core.asgi.application'

# Channel Layers (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# WebSocket settings
WEBSOCKET_ACCEPT_ALL = False  # Require authentication
```

---

### Step 3: Create ASGI Configuration

**core/asgi.py:**
```python
import os
from django.core.asgi import get_django_asgi_app
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from apps.dashboard.consumers import DashboardConsumer
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_django_asgi_app()

websocket_urlpatterns = [
    path('ws/dashboard/<str:user_id>/', DashboardConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

---

### Step 4: Create WebSocket Consumer

**apps/dashboard/consumers.py:**
```python
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    
    Handles:
    - Chart updates
    - Inventory alerts
    - Heatmap updates
    - Forecast notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'dashboard_{self.user_id}'
        
        # Verify user is authenticated
        user = await self.get_user(self.user_id)
        if not user:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user_id} connected to dashboard")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user_id} disconnected")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_sku':
                await self.subscribe_sku(data)
            elif message_type == 'unsubscribe_sku':
                await self.unsubscribe_sku(data)
            elif message_type == 'request_update':
                await self.request_update(data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
    
    # ===== Event Handlers (called from group_send) =====
    
    async def chart_update(self, event):
        """
        Broadcast chart update to client.
        Called when forecast is updated.
        """
        await self.send(text_data=json.dumps({
            'type': 'chart_update',
            'data': event['data'],
            'timestamp': event['timestamp'],
        }))
    
    async def inventory_alert(self, event):
        """
        Broadcast inventory alert to client.
        Called when stock level changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'inventory_alert',
            'alert_type': event['alert_type'],  # 'critical', 'warning', 'info'
            'message': event['message'],
            'sku': event['sku'],
            'timestamp': event['timestamp'],
        }))
    
    async def heatmap_update(self, event):
        """
        Broadcast heatmap update to client.
        Called when warehouse stock changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'heatmap_update',
            'data': event['data'],
            'timestamp': event['timestamp'],
        }))
    
    async def forecast_notification(self, event):
        """
        Broadcast forecast notification to client.
        Called when new forecast is available.
        """
        await self.send(text_data=json.dumps({
            'type': 'forecast_notification',
            'message': event['message'],
            'sku': event['sku'],
            'forecast': event['forecast'],
            'timestamp': event['timestamp'],
        }))
    
    # ===== Helper Methods =====
    
    @database_sync_to_async
    def get_user(self, user_id):
        """Get user from database."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    async def subscribe_sku(self, data):
        """Subscribe to specific SKU updates."""
        sku = data.get('sku')
        self.sku_group_name = f'sku_{sku}'
        
        await self.channel_layer.group_add(
            self.sku_group_name,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'sku': sku,
        }))
    
    async def unsubscribe_sku(self, data):
        """Unsubscribe from specific SKU updates."""
        sku = data.get('sku')
        sku_group_name = f'sku_{sku}'
        
        await self.channel_layer.group_discard(
            sku_group_name,
            self.channel_name
        )
    
    async def request_update(self, data):
        """Client requests fresh data."""
        # Fetch latest data and send
        pass
```

---

### Step 5: Create Signal Handlers to Trigger Events

**apps/dashboard/signals.py:**
```python
import json
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.asgi import get_asgi_application
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import InventoryHistory

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=InventoryHistory)
def inventory_updated(sender, instance, created, **kwargs):
    """
    Signal handler: When inventory is updated, broadcast to all connected clients.
    """
    if created:
        logger.info(f"Inventory updated: SKU={instance.item_id}")
        
        # Prepare event data
        event_data = {
            'type': 'chart_update',
            'data': {
                'sku': str(instance.item_id),
                'stock': float(instance.stock_quantity),
                'price': float(instance.price),
                'timestamp': instance.timestamp.isoformat(),
            },
            'timestamp': instance.timestamp.isoformat(),
        }
        
        # Broadcast to all dashboard users
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            event_data
        )
        
        # Broadcast to specific SKU subscribers
        async_to_sync(channel_layer.group_send)(
            f'sku_{instance.item_id}',
            event_data
        )
        
        # Check if alert needed
        check_inventory_alert(instance)


def check_inventory_alert(inventory):
    """Check if inventory alert should be triggered."""
    from .models import DimProducts
    
    try:
        product = DimProducts.objects.get(item_id=inventory.item_id)
        
        if inventory.stock_quantity < product.safety_stock_level:
            alert_type = 'critical'
            message = f"⚠️ CRITICAL: SKU {inventory.item_id} below safety stock!"
        elif inventory.stock_quantity < product.safety_stock_level * 1.5:
            alert_type = 'warning'
            message = f"⚠️ WARNING: SKU {inventory.item_id} approaching safety stock"
        else:
            return
        
        # Broadcast alert
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'inventory_alert',
                'alert_type': alert_type,
                'message': message,
                'sku': str(inventory.item_id),
                'timestamp': inventory.timestamp.isoformat(),
            }
        )
    except DimProducts.DoesNotExist:
        pass


# Register signals
from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    
    def ready(self):
        import apps.dashboard.signals
```

---

### Step 6: Update Views to Trigger Events

**apps/dashboard/views.py (Updated):**
```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


@login_required(login_url='login')
def simulator_view(request):
    """Mô phỏng nhập xuất kho (Updated with real-time)."""
    engine, _, _ = get_engine_instances()
    inventory_service = InventoryService(engine)
    
    # ... existing code ...
    
    if request.method == 'POST':
        # ... existing code ...
        
        try:
            if sim_type == 'outbound':
                new_stock_level = inventory_service.process_outbound(...)
            else:
                new_stock_level = inventory_service.process_inbound(...)
            
            # Reset cache
            reset_engine_cache()
            
            # ===== NEW: Broadcast real-time update =====
            async_to_sync(channel_layer.group_send)(
                'dashboard_updates',
                {
                    'type': 'chart_update',
                    'data': {
                        'sku': str(sim_sku_val),
                        'stock': new_stock_level,
                        'type': sim_type,
                        'quantity': sim_qty,
                    },
                    'timestamp': pd.Timestamp.now().isoformat(),
                }
            )
            
            transaction_success = True
            messages.success(request, f"Giao dịch thành công! Tồn kho mới: {new_stock_level}")
            
        except Exception as e:
            messages.error(request, sanitize_error(e, is_technical_admin(request.user)))
    
    return render(request, 'dashboard/simulator.html', {...})
```

---

### Step 7: Frontend WebSocket Connection

**core/templates/dashboard/home.html (Updated):**
```html
{% extends 'dashboard/dashboard_base.html' %}

{% block content %}
<div id="dashboard-container">
    <div id="chart-container">
        <div id="forecast-chart"></div>
    </div>
    
    <div id="alerts-container">
        <!-- Alerts will appear here -->
    </div>
    
    <div id="heatmap-container">
        <div id="warehouse-heatmap"></div>
    </div>
</div>

<script>
// WebSocket connection
const userId = "{{ request.user.id }}";
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${wsProtocol}//${window.location.host}/ws/dashboard/${userId}/`;

const socket = new WebSocket(wsUrl);

socket.onopen = function(e) {
    console.log('WebSocket connection established');
    
    // Subscribe to SKU updates
    const sku = document.getElementById('selected-sku').value;
    socket.send(JSON.stringify({
        type: 'subscribe_sku',
        sku: sku,
    }));
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'chart_update':
            updateChart(data.data);
            break;
        
        case 'inventory_alert':
            showAlert(data);
            break;
        
        case 'heatmap_update':
            updateHeatmap(data.data);
            break;
        
        case 'forecast_notification':
            showNotification(data);
            break;
    }
};

socket.onerror = function(error) {
    console.error('WebSocket error:', error);
};

socket.onclose = function(e) {
    console.log('WebSocket connection closed');
};

// Update chart in real-time
function updateChart(data) {
    console.log('Updating chart with:', data);
    
    // Update Plotly chart
    const update = {
        x: [[data.timestamp]],
        y: [[data.stock]],
    };
    
    Plotly.extendTraces('forecast-chart', update, [0]);
}

// Show alert notification
function showAlert(data) {
    const alertClass = data.alert_type === 'critical' ? 'alert-danger' : 'alert-warning';
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <strong>${data.alert_type.toUpperCase()}:</strong> ${data.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.getElementById('alerts-container').insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        document.querySelector('.alert').remove();
    }, 5000);
}

// Update heatmap
function updateHeatmap(data) {
    console.log('Updating heatmap with:', data);
    // Update heatmap visualization
}

// Show notification
function showNotification(data) {
    console.log('Notification:', data.message);
    // Show toast notification
}
</script>
{% endblock %}
```

---

## 🧪 Testing & Deployment

### Step 1: Test Locally

```bash
# Install Redis
# macOS: brew install redis
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server

# Run Django with Daphne
daphne -b 0.0.0.0 -p 8000 core.asgi:application

# Or use runserver with channels
python manage.py runserver
```

### Step 2: Test WebSocket Connection

```python
# test_websocket.py
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/dashboard/1/"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to SKU
        await websocket.send(json.dumps({
            'type': 'subscribe_sku',
            'sku': '7743986580',
        }))
        
        # Listen for messages
        async for message in websocket:
            print(f"Received: {message}")

asyncio.run(test_websocket())
```

### Step 3: Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## ⚡ Performance Optimization

### 1. Connection Pooling
```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 1500,
            'expiry': 10,
            'group_expiry': 86400,
        },
    },
}
```

### 2. Message Compression
```python
# Compress large messages before sending
import gzip
import base64

def compress_data(data):
    json_str = json.dumps(data)
    compressed = gzip.compress(json_str.encode())
    return base64.b64encode(compressed).decode()
```

### 3. Selective Broadcasting
```python
# Only broadcast to users viewing specific SKU
async_to_sync(channel_layer.group_send)(
    f'sku_{sku_id}',  # Specific group
    event_data
)
```

### 4. Rate Limiting
```python
# Prevent message flooding
from django.core.cache import cache

def rate_limit_check(user_id, limit=10, window=60):
    key = f'ws_rate_{user_id}'
    count = cache.get(key, 0)
    
    if count >= limit:
        return False
    
    cache.set(key, count + 1, window)
    return True
```

---

## 🔐 Security Considerations

### 1. WebSocket Authentication
```python
# consumers.py
async def connect(self):
    # Verify user is authenticated
    user = self.scope['user']
    if not user.is_authenticated:
        await self.close()
        return
```

### 2. JWT Token Validation
```python
# Validate JWT token in WebSocket
from rest_framework_simplejwt.tokens import AccessToken

def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        return access_token['user_id']
    except:
        return None
```

### 3. Rate Limiting
```python
# Prevent abuse
WEBSOCKET_RATE_LIMIT = 100  # messages per minute
```

---

## 📊 Monitoring & Logging

```python
# logging.py
import logging

logger = logging.getLogger('channels')
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('channels.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log WebSocket events
logger.info(f"User {user_id} connected")
logger.info(f"Message sent to {group_name}")
logger.error(f"WebSocket error: {error}")
```

---

## 🚀 Deployment

### Docker Compose
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 core.asgi:application
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: greenmind-channels
spec:
  replicas: 3
  selector:
    matchLabels:
      app: greenmind
  template:
    metadata:
      labels:
        app: greenmind
    spec:
      containers:
      - name: web
        image: greenmind:latest
        command: ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]
        ports:
        - containerPort: 8000
```

---

## 📈 Scaling Considerations

### Single Server
- Redis on same machine
- Daphne + Gunicorn
- Up to 1000 concurrent connections

### Multiple Servers
- Separate Redis instance
- Multiple Daphne instances behind load balancer
- Redis Cluster for high availability

### Enterprise Scale
- Redis Sentinel for failover
- Kafka for event streaming
- Separate WebSocket servers
- CDN for static assets

---

## 🎯 Implementation Checklist

- [ ] Install Django Channels & Redis
- [ ] Configure ASGI application
- [ ] Create WebSocket consumer
- [ ] Create signal handlers
- [ ] Update views to broadcast events
- [ ] Create frontend WebSocket connection
- [ ] Test locally
- [ ] Load testing
- [ ] Security audit
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Optimize based on metrics

---

## 📚 References

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Redis Pub/Sub Pattern](https://redis.io/topics/pubsub)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Plotly Real-Time Updates](https://plotly.com/javascript/streaming/)
- [Django Signals](https://docs.djangoproject.com/en/5.0/topics/signals/)

---

## 💡 Next Steps

1. **Phase 1:** Implement basic WebSocket connection (2-3 hours)
2. **Phase 2:** Add chart updates (2-3 hours)
3. **Phase 3:** Add alerts & notifications (2-3 hours)
4. **Phase 4:** Performance optimization (2-3 hours)
5. **Phase 5:** Deployment & monitoring (2-3 hours)

**Total Estimated Time:** 10-15 hours

---

**Last Updated:** May 26, 2026  
**Status:** Ready for Implementation
