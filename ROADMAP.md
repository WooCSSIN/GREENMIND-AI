# 🗺️ GreenMind AI - Product Roadmap 2026

**Last Updated:** May 26, 2026  
**Status:** Active Development

---

## 📊 Executive Summary

GreenMind AI có nền tảng tốt nhưng cần cải thiện trong 3 lĩnh vực chính:
1. **Performance & Scalability** - Xử lý multi-user, real-time updates
2. **AI/ML Advanced Features** - Explainability, AutoML, Anomaly Detection
3. **Enterprise Integration** - API, IoT, ERP, Cloud-ready

---

## 🎯 Strategic Priorities

### Q2 2026 (Current) - **Foundation & Stability**
- ✅ Fix critical bugs (authentication, chart cache)
- ✅ Clean up codebase
- ⏳ Improve test coverage
- ⏳ Optimize performance

### Q3 2026 - **Real-Time & Scalability**
- WebSocket/Real-time updates
- Redis caching
- Async job processing
- Multi-warehouse support

### Q4 2026 - **AI/ML Advanced**
- Model Explainability (SHAP/LIME)
- AutoML integration
- Anomaly Detection
- Advanced Analytics

### Q1 2027 - **Enterprise & Integration**
- Public REST API
- IoT integration
- ERP/Marketplace connectors
- Cloud deployment (Docker/K8s)

---

## 🔴 CRITICAL Issues (P0) - Fix Now

### 1. Performance Bottleneck: 3 ML Models Running in Parallel
**Impact:** High - Affects all users  
**Effort:** Medium (4-6 hours)  
**Status:** In Progress

**Problem:**
```python
# Current: Runs 3 models sequentially for every page load
def compare_models(item_id):
    results = {
        "SARIMAX": self.run_sarimax(train, test),      # ~1-2s
        "Prophet": self.run_prophet(train, test),      # ~1-2s
        "XGBoost": self.run_xgboost(train, test),      # ~1-2s
    }
    # Total: 3-6 seconds per SKU!
```

**Solutions (Priority Order):**
1. **Cache predictions in Redis** (Quick win)
   - Cache results for 1 hour
   - Invalidate on new transactions
   - Estimated: 2-3 hours

2. **Async job processing** (Medium-term)
   - Use Celery + Redis
   - Run models in background
   - Return cached results
   - Estimated: 4-6 hours

3. **Only compute champion model at runtime** (Alternative)
   - Pre-compute all models daily
   - Return only champion at runtime
   - Estimated: 2-3 hours

**Acceptance Criteria:**
- [ ] Dashboard load time < 2 seconds
- [ ] Multi-user concurrent access works
- [ ] Cache invalidation on transactions
- [ ] Performance tests pass

---

### 2. Chart Cache Not Updating After Transactions
**Impact:** High - User-facing bug  
**Effort:** Low (1-2 hours)  
**Status:** Partially Fixed

**Current Status:**
- ✅ Implemented `reset_engine_cache()` function
- ⏳ Need to test thoroughly
- ⏳ Need to verify performance

**Remaining Tasks:**
- [ ] Test with multiple concurrent transactions
- [ ] Verify chart updates immediately
- [ ] Add integration tests
- [ ] Monitor performance

---

### 3. Authentication Logic - Dual Auth System
**Impact:** High - Security risk  
**Effort:** Medium (2-3 hours)  
**Status:** Not Started

**Problem:**
- Dual authentication (Django + SQL Server)
- Dim_Users table marked DEPRECATED but still used
- Security risk with 2x attack surface

**Solution:**
- Remove Dim_Users sync
- Use Django auth only
- Create UserProfile model

**Acceptance Criteria:**
- [ ] Login/register works with Django only
- [ ] No Dim_Users sync
- [ ] All tests pass
- [ ] Security audit passed

---

## 🟡 IMPORTANT Issues (P1) - Next Sprint

### 4. Real-Time Updates with WebSocket
**Impact:** Medium - UX improvement  
**Effort:** High (8-12 hours)  
**Status:** Not Started

**Solution Options:**

**Option A: Django Channels (Recommended)**
```python
# Real-time chart updates
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("dashboard", self.channel_name)
        await self.accept()
    
    async def chart_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
```

**Option B: Redis Pub/Sub**
- Simpler than Channels
- Good for notifications
- Estimated: 4-6 hours

**Option C: Server-Sent Events (SSE)**
- Simpler than WebSocket
- Good for one-way updates
- Estimated: 2-3 hours

**Recommendation:** Start with SSE (quick), then upgrade to Channels (full real-time)

**Acceptance Criteria:**
- [ ] Real-time chart updates
- [ ] Notifications on transactions
- [ ] Mobile app can receive push
- [ ] Performance acceptable

---

### 5. Multi-Warehouse Support
**Impact:** Medium - Business requirement  
**Effort:** High (12-16 hours)  
**Status:** Not Started

**Current Limitation:**
- Single warehouse only
- No cross-warehouse inventory sync
- No supplier/marketplace integration

**Solution:**
1. Add `warehouse_id` to Dim_Products
2. Add warehouse selection in UI
3. Aggregate forecasts across warehouses
4. Add transfer between warehouses

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
```

**Acceptance Criteria:**
- [ ] Multiple warehouses supported
- [ ] Inventory sync between warehouses
- [ ] Forecasts aggregated correctly
- [ ] UI supports warehouse selection

---

### 6. Improve Test Coverage
**Impact:** Medium - Code quality  
**Effort:** Medium (6-8 hours)  
**Status:** In Progress

**Current Status:**
- Basic security tests exist
- Inventory tests exist
- AI model tests missing
- Integration tests missing

**Target Coverage:**
- Overall: 70%+
- Critical paths: 90%+
- AI models: 60%+

**Tests to Add:**
- [ ] Model comparison tests
- [ ] Forecast accuracy tests
- [ ] Cache invalidation tests
- [ ] Multi-user concurrent tests
- [ ] API endpoint tests
- [ ] Integration tests

---

## 🟢 NICE TO HAVE Issues (P2) - Future

### 7. Model Explainability (SHAP/LIME)
**Impact:** Low - Nice to have  
**Effort:** High (12-16 hours)  
**Status:** Not Started

**Solution:**
```python
import shap

def explain_prediction(model, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    return shap_values

# In dashboard:
# Show SHAP force plot explaining why forecast is X
```

**Benefits:**
- Users understand why system predicts certain values
- Build trust in AI
- Identify feature importance

---

### 8. AutoML Integration
**Impact:** Low - Nice to have  
**Effort:** High (16-20 hours)  
**Status:** Not Started

**Options:**
1. **Optuna** - Hyperparameter tuning
2. **FLAML** - Fast AutoML
3. **Auto-sklearn** - Full AutoML

**Implementation:**
```python
from optuna import create_study

def optimize_xgboost(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
    }
    model = xgb.XGBRegressor(**params)
    return cross_val_score(model, X, y).mean()

study = create_study()
study.optimize(optimize_xgboost, n_trials=100)
```

---

### 9. Anomaly Detection
**Impact:** Low - Nice to have  
**Effort:** Medium (8-10 hours)  
**Status:** Not Started

**Solution:**
```python
from sklearn.ensemble import IsolationForest

def detect_anomalies(data):
    iso_forest = IsolationForest(contamination=0.1)
    anomalies = iso_forest.fit_predict(data)
    return anomalies

# Alert on:
# - Unusual demand spikes
# - Inventory discrepancies
# - Fraud detection
```

---

### 10. Public REST API
**Impact:** Medium - Business value  
**Effort:** Medium (8-10 hours)  
**Status:** Partially Done

**Current Status:**
- ✅ DRF setup
- ✅ JWT auth
- ⏳ Limited endpoints
- ⏳ No public documentation

**Endpoints to Add:**
```
GET    /api/v1/products/
GET    /api/v1/products/{id}/
GET    /api/v1/forecasts/{product_id}/
GET    /api/v1/inventory/{product_id}/
POST   /api/v1/transactions/
GET    /api/v1/esg-metrics/
```

**Documentation:**
- [ ] OpenAPI/Swagger spec
- [ ] API client SDK (Python)
- [ ] Usage examples
- [ ] Rate limiting docs

---

### 11. IoT Integration
**Impact:** Low - Future feature  
**Effort:** High (16-20 hours)  
**Status:** Not Started

**Solution:**
- MQTT broker for sensor data
- Real-time stock level updates
- Temperature/humidity monitoring
- Automatic alerts

---

### 12. Cloud Deployment (Docker/K8s)
**Impact:** Medium - DevOps  
**Effort:** Medium (8-10 hours)  
**Status:** Not Started

**Deliverables:**
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline
- [ ] Deployment guide

---

### 13. ERP/Marketplace Integration
**Impact:** Medium - Business value  
**Effort:** High (16-20 hours)  
**Status:** Not Started

**Integrations:**
- Shopee API (already have data)
- Lazada API
- SAP/Oracle ERP
- Excel import/export

---

### 14. Carbon Footprint API Integration
**Impact:** Low - ESG feature  
**Effort:** Medium (6-8 hours)  
**Status:** Not Started

**APIs to Integrate:**
- Carbon Trust API
- EPA Emissions API
- Local grid emission factors

---

## 📈 Effort vs Impact Matrix

```
HIGH IMPACT, LOW EFFORT (Do First):
- Fix chart cache ✅
- Performance optimization (caching)
- Real-time updates (SSE)
- Improve tests

HIGH IMPACT, HIGH EFFORT (Plan):
- Multi-warehouse support
- Public API
- AutoML
- Cloud deployment

LOW IMPACT, LOW EFFORT (Quick Wins):
- Documentation
- Code cleanup
- Minor UI improvements

LOW IMPACT, HIGH EFFORT (Avoid):
- Anomaly detection (for now)
- IoT (for now)
- Advanced explainability (for now)
```

---

## 🎯 Recommended Execution Plan

### **Phase 1: Stability (2 weeks)**
1. Fix authentication (Issue #1)
2. Clean up debug files (Issue #2)
3. Verify chart cache fix (Issue #3)
4. Improve test coverage

### **Phase 2: Performance (3 weeks)**
1. Implement Redis caching
2. Add async job processing
3. Performance testing
4. Load testing

### **Phase 3: Real-Time (2 weeks)**
1. Implement SSE for real-time updates
2. Add WebSocket (optional)
3. Mobile push notifications

### **Phase 4: Enterprise (4 weeks)**
1. Multi-warehouse support
2. Public REST API
3. ERP integration
4. Cloud deployment

### **Phase 5: Advanced AI (4 weeks)**
1. Model explainability
2. AutoML integration
3. Anomaly detection
4. Advanced analytics

---

## 📊 Success Metrics

### Performance
- Dashboard load time: < 2 seconds
- API response time: < 500ms
- Concurrent users: 100+

### Quality
- Test coverage: 70%+
- Bug fix time: < 24 hours
- Uptime: 99.5%+

### Business
- User satisfaction: 4.5+/5
- Feature adoption: 80%+
- Revenue impact: TBD

---

## 🤝 Contributing

To contribute to this roadmap:
1. Create an issue with your proposal
2. Add to appropriate priority level
3. Discuss with team
4. Add to sprint planning

---

## 📞 Questions?

- **Technical:** Create an issue with `[QUESTION]` tag
- **Business:** Contact product team
- **Bugs:** Create bug report

---

**Next Review:** June 30, 2026
