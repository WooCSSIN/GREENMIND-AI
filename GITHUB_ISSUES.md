# GitHub Issues Tracker

Dựa trên SYSTEM_ANALYSIS_REPORT, dưới đây là danh sách issues cần tạo trên GitHub:

## 🔴 CRITICAL Issues

### Issue 1: Fix Authentication Logic - Remove Dual Auth System
**Title:** [CRITICAL] Remove dual authentication with Dim_Users  
**Labels:** critical, refactor, security  
**Priority:** P0  
**Assignee:** @WooCSSIN  

**Description:**
- Remove Dim_Users sync logic from login_view
- Remove SHA256 hashing for SQL Server
- Remove SQL Server auth check
- Create UserProfile model for additional user info
- Update Fact_Inventory_History.UserID to reference Django User.id

**Acceptance Criteria:**
- [ ] Login/register works with Django auth only
- [ ] No more Dim_Users sync
- [ ] All tests pass
- [ ] Security audit passed

**Estimated Time:** 2-3 hours

---

### Issue 2: Clean Up Debug Files and Temporary Code
**Title:** [CRITICAL] Remove debug files and tmp/ folder  
**Labels:** critical, cleanup  
**Priority:** P0  
**Assignee:** @WooCSSIN  

**Description:**
Remove all temporary debug files:
- Delete tmp/ folder (14 files)
- Delete root debug files: check_*.py, debug_*.py
- Update .gitignore to prevent future debug files
- Backup if needed

**Files to Delete:**
```
tmp/check_db_schema.py
tmp/check_dim_users.py
tmp/check_products.py
tmp/check_simulation_results.py
tmp/check_sp.py
tmp/check_user_table.py
tmp/reproduce_reg_error.py
tmp/run_real_simulate.py
tmp/run_transaction.py
tmp/save_reg_error.py
tmp/setup_admin.py
tmp/test_map_sync.py
tmp/test_reg_post.py
tmp/test_reg_urllib.py
tmp/verify_system_logs.py

Root:
check_grid_0.py
check_macbook.py
check_macbook_v2.py
debug_sku.py
```

**Acceptance Criteria:**
- [ ] All debug files deleted
- [ ] .gitignore updated
- [ ] No sensitive info leaked
- [ ] Codebase cleaner

**Estimated Time:** 30 minutes

---

### Issue 3: Fix Chart Cache Not Updating After Transactions
**Title:** [CRITICAL] Dashboard chart not updating after inventory transactions  
**Labels:** critical, bug, performance  
**Priority:** P0  
**Assignee:** @WooCSSIN  

**Description:**
After inbound/outbound transactions in simulator, the dashboard chart doesn't reflect the new data. The global engine cache is not being reset properly.

**Root Cause:**
```python
# Current issue:
_engine = None  # Global cache
def get_engine_instances():
    if _engine is None:
        _engine = GreenMindEngine()
    return _engine  # Returns cached instance

# After transaction:
engine.load_data()  # Reloads this instance
# But home_view still uses cached _engine from before!
```

**Solution:**
Implement force_reload parameter and reset cache after transactions.

**Acceptance Criteria:**
- [ ] Implement force_reload parameter
- [ ] Reset cache after simulator transactions
- [ ] Dashboard updates immediately after inbound/outbound
- [ ] Test with multiple transactions
- [ ] Performance acceptable (<3 seconds)

**Estimated Time:** 1-2 hours

---

## 🟡 IMPORTANT Issues

### Issue 4: Consolidate Documentation
**Title:** [IMPORTANT] Consolidate and clean up documentation  
**Labels:** documentation, cleanup  
**Priority:** P1  
**Assignee:** @WooCSSIN  

**Description:**
- Delete ISSUES_TODO.md (outdated)
- Merge SECURITY_FIXES.md into SECURITY_AUDIT_REPORT.md
- Move project_proposal.txt to docs/archive/
- Keep only essential docs: README, DEPLOYMENT, SECURITY, TECHNICAL_ARCHITECTURE

**Acceptance Criteria:**
- [ ] Outdated docs removed
- [ ] Security docs consolidated
- [ ] Archive folder created
- [ ] No broken references

**Estimated Time:** 1 hour

---

### Issue 5: Clean Up Notebooks Folder
**Title:** [IMPORTANT] Remove or organize notebooks folder  
**Labels:** cleanup  
**Priority:** P1  
**Assignee:** @WooCSSIN  

**Description:**
- Check notebooks/modeling/ folder
- If empty, delete folder
- If has notebooks, move to docs/research/
- Update README references

**Acceptance Criteria:**
- [ ] Notebooks organized or removed
- [ ] No broken references
- [ ] README updated

**Estimated Time:** 30 minutes

---

### Issue 6: Test Error Handlers
**Title:** [IMPORTANT] Test and verify 404/500 error pages  
**Labels:** testing, quality  
**Priority:** P1  
**Assignee:** @WooCSSIN  

**Description:**
- Test 404 page: Access non-existent URL
- Test 500 page: Trigger exception in view
- Verify error pages display correctly in production (DEBUG=False)
- Add test cases for error handlers

**Acceptance Criteria:**
- [ ] 404 page displays correctly
- [ ] 500 page displays correctly
- [ ] Test cases added
- [ ] Works in production mode

**Estimated Time:** 1 hour

---

## 🟢 NICE TO HAVE Issues

### Issue 7: Add Logging Configuration
**Title:** [ENHANCEMENT] Add comprehensive logging configuration  
**Labels:** enhancement, logging  
**Priority:** P2  

**Description:**
Add logging config to settings.py for security logger and application logs.

---

### Issue 8: Add CORS Warning Log
**Title:** [ENHANCEMENT] Add warning log for CORS_ALLOW_ALL_ORIGINS  
**Labels:** enhancement, security  
**Priority:** P2  

**Description:**
Add warning when CORS_ALLOW_ALL_ORIGINS is True in DEBUG mode.

---

### Issue 9: Performance Optimization - ML Model Caching
**Title:** [ENHANCEMENT] Optimize ML model performance with caching  
**Labels:** enhancement, performance  
**Priority:** P2  

**Description:**
- Cache ML model results in Redis
- Reduce redundant model training
- Implement cache invalidation strategy

---

### Issue 10: Add Redis Caching for Distributed Systems
**Title:** [ENHANCEMENT] Implement Redis caching for multi-worker deployment  
**Labels:** enhancement, performance, scaling  
**Priority:** P2  

**Description:**
Replace global mutable state with Redis for distributed Gunicorn workers.

---

## 📊 Priority Matrix

| Priority | Count | Issues |
|----------|-------|--------|
| P0 (Critical) | 3 | #1, #2, #3 |
| P1 (Important) | 3 | #4, #5, #6 |
| P2 (Nice to have) | 4 | #7, #8, #9, #10 |

---

## 🎯 Recommended Execution Order

1. **Week 1 (Critical)**
   - Issue #2: Clean up debug files (30 min)
   - Issue #1: Fix authentication (2-3 hours)
   - Issue #3: Fix chart cache (1-2 hours)

2. **Week 2 (Important)**
   - Issue #4: Consolidate docs (1 hour)
   - Issue #5: Clean notebooks (30 min)
   - Issue #6: Test error handlers (1 hour)

3. **Week 3+ (Nice to have)**
   - Issue #7-10: Performance & enhancements

---

## 📝 How to Create Issues on GitHub

1. Go to: https://github.com/WooCSSIN/GREENMIND-AI/issues
2. Click "New Issue"
3. Copy the issue description from above
4. Add labels and assignee
5. Click "Submit new issue"

Or use GitHub CLI:
```bash
gh issue create --title "Issue Title" --body "Issue description" --label "label1,label2"
```

---

**Last Updated:** May 26, 2026  
**Total Issues:** 10  
**Estimated Total Time:** 8-10 hours
