# 📋 Detailed Issues from Analysis

Dựa trên phân tích chi tiết của bạn, dưới đây là danh sách issues cần tạo trên GitHub.

---

## 🔴 CRITICAL (P0) - Fix Immediately

### Issue #1: [CRITICAL] Performance Bottleneck - 3 ML Models Running in Parallel

**Labels:** `critical`, `performance`, `ai`  
**Assignee:** @WooCSSIN  
**Effort:** 4-6 hours  

**Description:**

When loading dashboard, the system runs 3 ML models (SARIMAX, Prophet, XGBoost) sequentially, taking 3-6 seconds per SKU. This is unacceptable for multi-user environments.

**Current Code:**
```python
def compare_models(item_id, test_size=0.2):
    # Runs 3 models sequentially
    results = {
        "SARIMAX": self.run_sarimax(train, test),      # ~1-2s
        "Prophet": self.run_prophet(train, test),      # ~1-2s
        "XGBoost": self.run_xgboost(train, test),      # ~1-2s
    }
    # Total: 3-6 seconds!
```

**Solutions (in priority order):**

**Solution 1: Redis Caching (Recommended - Quick Win)**
- Cache model results for 1 hour
- Invalidate on new transactions
- Estimated: 2-3 hours
- Impact: 80% improvement

**Solution 2: Async Job Processing**
- Use Celery + Redis
- Run models in background
- Return cached results
- Estimated: 4-6 hours
- Impact: 90% improvement

**Solution 3: Champion Model Only**
- Pre-compute all models daily
- Return only champion at runtime
- Estimated: 2-3 hours
- Impact: 70% improvement

**Acceptance Criteria:**
- [ ] Dashboard load time < 2 seconds
- [ ] Multi-user concurrent access works
- [ ] Cache invalidation on transactions
- [ ] Performance tests pass (load test with 10+ concurrent users)
- [ ] No data loss or stale predictions

**Testing:**
```bash
# Load test
ab -n 100 -c 10 http://localhost:8000/dashboard/

# Expected: < 2 seconds per request
```

---

### Issue #2: [CRITICAL] Chart Cache Not Updating After Transactions

**Labels:** `critical`, `bug`, `ui`  
**Assignee:** @WooCSSIN  
**Effort:** 1-2 hours  
**Status:** Partially Fixed

**Description:**

After inbound/outbound transactions in simulator, the dashboard chart doesn't reflect the new data. The global engine cache is not being reset properly.

**Current Status:**
- ✅ Implemented `reset_engine_cache()` function in views.py
- ⏳ Need thorough testing
- ⏳ Need integration tests

**Remaining Tasks:**
- [ ] Test with multiple concurrent transactions
- [ ] Verify chart updates immediately after transaction
- [ ] Add integration tests
- [ ] Monitor performance impact
- [ ] Test with different SKUs
- [ ] Test with rapid transactions

**Test Cases:**
```python
def test_chart_updates_after_inbound():
    # 1. Get initial chart data
    # 2. Perform inbound transaction
    # 3. Refresh dashboard
    # 4. Verify chart shows new data
    pass

def test_chart_updates_after_outbound():
    # Similar to above
    pass

def test_concurrent_transactions():
    # Multiple users doing transactions simultaneously
    # Verify all see updated charts
    pass
```

**Acceptance Criteria:**
- [ ] Chart updates immediately after transaction
- [ ] No stale data shown
- [ ] Performance acceptable
- [ ] All tests pass
- [ ] Works with concurrent users

---

### Issue #3: [CRITICAL] Remove Dual Authentication System

**Labels:** `critical`, `security`, `refactor`  
**Assignee:** @WooCSSIN  
**Effort:** 2-3 hours  

**Description:**

The system uses dual authentication (Django + SQL Server), which is:
- Unnecessarily complex
- A security risk (2x attack surface)
- Hard to maintain (sync issues)
- Performance overhead

**Current Implementation:**
```python
# WRONG: Dual auth
def login_view(request):
    # 1. Check Django User
    user = authenticate(username=u, password=p)
    # 2. Also check SQL Server Dim_Users
    # 3. Sync passwords with SHA256
    # This is wrong!
```

**Solution:**
Use Django auth only, remove Dim_Users sync.

**Tasks:**
- [ ] Remove Dim_Users sync from login_view
- [ ] Remove SHA256 hashing for SQL Server
- [ ] Remove SQL Server auth check
- [ ] Create UserProfile model for additional user info
- [ ] Update Fact_Inventory_History.UserID to reference Django User.id
- [ ] Update all views to use Django User
- [ ] Run all tests
- [ ] Security audit

**Code Changes:**
```python
# CORRECT: Single auth
def login_view(request):
    user = authenticate(username=u, password=p)
    if user:
        login(request, user)
        return redirect('home')
```

**Acceptance Criteria:**
- [ ] Login/register works with Django auth only
- [ ] No more Dim_Users sync
- [ ] All tests pass
- [ ] Security audit passed
- [ ] No data loss

---

## 🟡 IMPORTANT (P1) - Next Sprint

### Issue #4: [IMPORTANT] Real-Time Updates with WebSocket/SSE

**Labels:** `important`, `feature`, `ui`  
**Assignee:** TBD  
**Effort:** 8-12 hours  

**Description:**

Currently, dashboard uses polling (page refresh). Need real-time updates when:
- New transactions occur
- Forecasts update
- Alerts triggered
- Inventory changes

**Solution Options:**

**Option A: Server-Sent Events (SSE) - Recommended First**
- Simpler than WebSocket
- Good for one-way updates
- Estimated: 2-3 hours
- Browser support: Excellent

**Option B: Django Channels (WebSocket)**
- Full real-time bidirectional
- More complex
- Estimated: 8-10 hours
- Better for interactive features

**Option C: Redis Pub/Sub**
- Good for notifications
- Simpler than Channels
- Estimated: 4-6 hours

**Recommendation:** Start with SSE, upgrade to Channels later.

**Implementation (SSE):**
```python
# views.py
from django.http import StreamingHttpResponse

def dashboard_stream(request):
    def event_stream():
        while True:
            # Get latest data
            data = get_latest_dashboard_data()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
    
    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

# template
<script>
const eventSource = new EventSource('/api/dashboard-stream/');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateChart(data);
};
</script>
```

**Acceptance Criteria:**
- [ ] Real-time chart updates
- [ ] Notifications on transactions
- [ ] Mobile app can receive push
- [ ] Performance acceptable
- [ ] No memory leaks

---

### Issue #5: [IMPORTANT] Multi-Warehouse Support

**Labels:** `important`, `feature`, `business`  
**Assignee:** TBD  
**Effort:** 12-16 hours  

**Description:**

Currently supports only single warehouse. Need to support:
- Multiple warehouses
- Cross-warehouse inventory sync
- Warehouse selection in UI
- Aggregate forecasts

**Database Changes:**
```sql
ALTER TABLE Dim_Products ADD warehouse_id INT;
ALTER TABLE Fact_Inventory_History ADD warehouse_id INT;

CREATE TABLE Warehouse_Transfers (
    transfer_id INT PRIMARY KEY,
    from_warehouse_id INT,
    to_warehouse_id INT,
    item_id BIGINT,
    quantity FLOAT,
    timestamp DATETIME
);

CREATE TABLE Warehouses (
    warehouse_id INT PRIMARY KEY,
    name NVARCHAR(255),
    location NVARCHAR(255),
    capacity FLOAT,
    is_active BIT
);
```

**UI Changes:**
- Add warehouse selector dropdown
- Show warehouse-specific inventory
- Add transfer between warehouses

**Acceptance Criteria:**
- [ ] Multiple warehouses supported
- [ ] Inventory sync between warehouses
- [ ] Forecasts aggregated correctly
- [ ] UI supports warehouse selection
- [ ] All tests pass

---

### Issue #6: [IMPORTANT] Improve Test Coverage to 70%+

**Labels:** `important`, `testing`, `quality`  
**Assignee:** TBD  
**Effort:** 6-8 hours  

**Description:**

Current test coverage is low. Need to add tests for:
- Model comparison
- Forecast accuracy
- Cache invalidation
- Multi-user concurrent access
- API endpoints
- Integration tests

**Current Status:**
- Basic security tests: ✅
- Inventory tests: ✅
- AI model tests: ❌
- Integration tests: ❌
- API tests: ❌

**Tests to Add:**
```python
# tests/test_models.py
def test_sarimax_forecast():
    pass

def test_prophet_forecast():
    pass

def test_xgboost_forecast():
    pass

def test_model_comparison():
    pass

# tests/test_cache.py
def test_cache_invalidation():
    pass

def test_cache_performance():
    pass

# tests/test_api.py
def test_forecast_api():
    pass

def test_inventory_api():
    pass

# tests/test_integration.py
def test_transaction_to_chart_update():
    pass

def test_concurrent_users():
    pass
```

**Acceptance Criteria:**
- [ ] Overall coverage: 70%+
- [ ] Critical paths: 90%+
- [ ] AI models: 60%+
- [ ] All tests pass
- [ ] CI/CD integration

---

## 🟢 NICE TO HAVE (P2) - Future

### Issue #7: [ENHANCEMENT] Model Explainability (SHAP/LIME)

**Labels:** `enhancement`, `ai`, `ux`  
**Effort:** 12-16 hours  

**Description:**

Add explainability to AI predictions so users understand why system predicts certain values.

**Implementation:**
```python
import shap

def explain_prediction(model, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    return shap_values

# In dashboard:
# Show SHAP force plot explaining why forecast is X
```

---

### Issue #8: [ENHANCEMENT] AutoML Integration

**Labels:** `enhancement`, `ai`  
**Effort:** 16-20 hours  

**Description:**

Automatically tune hyperparameters and select best model using Optuna or FLAML.

**Implementation:**
```python
from optuna import create_study

def optimize_xgboost(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
    }
    model = xgb.XGBRegressor(**params)
    return cross_val_score(model, X, y).mean()

study = create_study()
study.optimize(optimize_xgboost, n_trials=100)
```

---

### Issue #9: [ENHANCEMENT] Anomaly Detection

**Labels:** `enhancement`, `ai`, `alert`  
**Effort:** 8-10 hours  

**Description:**

Detect unusual patterns in inventory/transactions:
- Unusual demand spikes
- Inventory discrepancies
- Fraud detection

---

### Issue #10: [ENHANCEMENT] Public REST API

**Labels:** `enhancement`, `api`, `business`  
**Effort:** 8-10 hours  

**Description:**

Expose full AI functionality via public REST API.

**Endpoints:**
```
GET    /api/v1/products/
GET    /api/v1/products/{id}/
GET    /api/v1/forecasts/{product_id}/
GET    /api/v1/inventory/{product_id}/
POST   /api/v1/transactions/
GET    /api/v1/esg-metrics/
```

**Deliverables:**
- [ ] OpenAPI/Swagger spec
- [ ] API client SDK (Python)
- [ ] Usage examples
- [ ] Rate limiting docs

---

### Issue #11: [ENHANCEMENT] IoT Integration

**Labels:** `enhancement`, `iot`, `hardware`  
**Effort:** 16-20 hours  

**Description:**

Integrate with IoT sensors for real-time stock level updates.

**Features:**
- MQTT broker for sensor data
- Real-time stock level updates
- Temperature/humidity monitoring
- Automatic alerts

---

### Issue #12: [ENHANCEMENT] Cloud Deployment (Docker/K8s)

**Labels:** `enhancement`, `devops`, `deployment`  
**Effort:** 8-10 hours  

**Description:**

Prepare for cloud deployment with Docker and Kubernetes.

**Deliverables:**
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline
- [ ] Deployment guide

---

### Issue #13: [ENHANCEMENT] ERP/Marketplace Integration

**Labels:** `enhancement`, `integration`, `business`  
**Effort:** 16-20 hours  

**Description:**

Integrate with popular ERP and marketplace platforms.

**Integrations:**
- Shopee API
- Lazada API
- SAP/Oracle ERP
- Excel import/export

---

### Issue #14: [ENHANCEMENT] Carbon Footprint API Integration

**Labels:** `enhancement`, `esg`, `api`  
**Effort:** 6-8 hours  

**Description:**

Integrate with real carbon footprint APIs for accurate ESG metrics.

**APIs:**
- Carbon Trust API
- EPA Emissions API
- Local grid emission factors

---

## 📊 Priority Matrix

| Priority | Count | Issues | Total Effort |
|----------|-------|--------|--------------|
| P0 (Critical) | 3 | #1, #2, #3 | 7-11 hours |
| P1 (Important) | 3 | #4, #5, #6 | 26-36 hours |
| P2 (Nice to have) | 8 | #7-14 | 90-120 hours |

---

## 🎯 Recommended Execution Order

### **Week 1-2 (Critical - 7-11 hours)**
1. Issue #2: Fix chart cache (1-2 hours)
2. Issue #3: Remove dual auth (2-3 hours)
3. Issue #1: Performance optimization (4-6 hours)

### **Week 3-4 (Important - 26-36 hours)**
1. Issue #6: Improve tests (6-8 hours)
2. Issue #4: Real-time updates (8-12 hours)
3. Issue #5: Multi-warehouse (12-16 hours)

### **Week 5+ (Nice to have - 90-120 hours)**
1. Issue #10: Public API (8-10 hours)
2. Issue #12: Cloud deployment (8-10 hours)
3. Issue #7-9, #11, #13-14: Advanced features

---

## 📝 How to Create Issues

See `CREATE_GITHUB_ISSUES.md` for detailed instructions.

Quick command:
```bash
gh issue create \
  --title "[CRITICAL] Performance Bottleneck - 3 ML Models" \
  --body "See DETAILED_ISSUES.md for full description" \
  --label "critical,performance,ai"
```

---

**Total Estimated Effort:** 123-167 hours (3-4 months for 1 developer)

**Recommended Team:** 2-3 developers

**Timeline:** 
- Critical: 1-2 weeks
- Important: 3-4 weeks
- Nice to have: 2-3 months
