# 📋 Hướng dẫn Tạo GitHub Issues

Dựa trên GITHUB_ISSUES.md, dưới đây là hướng dẫn chi tiết để tạo issues trên GitHub.

## 🚀 Cách 1: Tạo Issues Thủ Công (Web UI)

### Bước 1: Truy cập GitHub Issues
1. Vào: https://github.com/WooCSSIN/GREENMIND-AI/issues
2. Click nút **"New issue"** (màu xanh)

### Bước 2: Tạo Issue #1 - Fix Authentication Logic

**Title:**
```
[CRITICAL] Remove dual authentication with Dim_Users
```

**Description:**
```markdown
## Problem
The system currently uses dual authentication (Django + SQL Server), which is:
- Unnecessarily complex
- A security risk (2x attack surface)
- Hard to maintain (sync issues)
- Performance overhead

## Solution
Remove Dim_Users sync logic and use Django auth only.

## Tasks
- [ ] Remove Dim_Users sync from login_view
- [ ] Remove SHA256 hashing for SQL Server
- [ ] Remove SQL Server auth check
- [ ] Create UserProfile model for additional user info
- [ ] Update Fact_Inventory_History.UserID to reference Django User.id
- [ ] Run all tests
- [ ] Security audit

## Acceptance Criteria
- [ ] Login/register works with Django auth only
- [ ] No more Dim_Users sync
- [ ] All tests pass
- [ ] Security audit passed

## Estimated Time
2-3 hours
```

**Labels:** `critical`, `refactor`, `security`  
**Assignee:** @WooCSSIN  
**Priority:** P0

---

### Bước 3: Tạo Issue #2 - Clean Up Debug Files

**Title:**
```
[CRITICAL] Remove debug files and tmp/ folder
```

**Description:**
```markdown
## Problem
Codebase contains many temporary debug files that:
- Make the project messy
- May contain hardcoded credentials
- Are not tracked in .gitignore properly
- Confuse new developers

## Files to Delete
- tmp/auto_check.py
- scripts/debug_ai_pipeline.py
- Any other check_*.py or debug_*.py files

## Tasks
- [ ] Delete tmp/ folder
- [ ] Delete root debug files
- [ ] Update .gitignore
- [ ] Verify no sensitive info leaked

## Acceptance Criteria
- [ ] All debug files deleted
- [ ] .gitignore updated
- [ ] No sensitive info leaked
- [ ] Codebase cleaner

## Estimated Time
30 minutes
```

**Labels:** `critical`, `cleanup`  
**Assignee:** @WooCSSIN  
**Priority:** P0

---

### Bước 4: Tạo Issue #3 - Fix Chart Cache

**Title:**
```
[CRITICAL] Dashboard chart not updating after inventory transactions
```

**Description:**
```markdown
## Problem
After inbound/outbound transactions in simulator, the dashboard chart doesn't reflect the new data.

## Root Cause
The global engine cache is not being reset properly:
```python
_engine = None  # Global cache
def get_engine_instances():
    if _engine is None:
        _engine = GreenMindEngine()
    return _engine  # Returns cached instance

# After transaction:
engine.load_data()  # Reloads this instance
# But home_view still uses cached _engine from before!
```

## Solution
Implement force_reload parameter and reset cache after transactions.

## Tasks
- [ ] Implement reset_engine_cache() function
- [ ] Add force_reload parameter to get_engine_instances()
- [ ] Call reset_engine_cache() after simulator transactions
- [ ] Call reset_engine_cache() after catalog changes
- [ ] Test with multiple transactions
- [ ] Verify performance acceptable

## Acceptance Criteria
- [ ] Dashboard updates immediately after inbound/outbound
- [ ] Test with multiple transactions
- [ ] Performance acceptable (<3 seconds)
- [ ] All tests pass

## Estimated Time
1-2 hours
```

**Labels:** `critical`, `bug`, `performance`  
**Assignee:** @WooCSSIN  
**Priority:** P0

---

## 🔧 Cách 2: Tạo Issues Bằng GitHub CLI (Nhanh hơn)

### Cài đặt GitHub CLI
```bash
# Windows (Chocolatey)
choco install gh

# macOS (Homebrew)
brew install gh

# Linux
sudo apt install gh
```

### Authenticate
```bash
gh auth login
# Chọn GitHub.com
# Chọn HTTPS
# Chọn Y để authenticate
```

### Tạo Issues Bằng CLI

**Issue #1:**
```bash
gh issue create \
  --title "[CRITICAL] Remove dual authentication with Dim_Users" \
  --body "See GITHUB_ISSUES.md for full description" \
  --label "critical,refactor,security" \
  --assignee "@WooCSSIN"
```

**Issue #2:**
```bash
gh issue create \
  --title "[CRITICAL] Remove debug files and tmp/ folder" \
  --body "See GITHUB_ISSUES.md for full description" \
  --label "critical,cleanup" \
  --assignee "@WooCSSIN"
```

**Issue #3:**
```bash
gh issue create \
  --title "[CRITICAL] Dashboard chart not updating after inventory transactions" \
  --body "See GITHUB_ISSUES.md for full description" \
  --label "critical,bug,performance" \
  --assignee "@WooCSSIN"
```

---

## 📊 Tạo Project Board (Optional)

### Bước 1: Tạo Project
1. Vào: https://github.com/WooCSSIN/GREENMIND-AI/projects
2. Click **"New project"**
3. Chọn **"Table"** template
4. Tên: "GreenMind Roadmap"

### Bước 2: Thêm Columns
- **Backlog** - Chưa bắt đầu
- **In Progress** - Đang làm
- **In Review** - Chờ review
- **Done** - Hoàn thành

### Bước 3: Thêm Issues vào Project
1. Vào issue
2. Click **"Projects"** ở sidebar
3. Chọn project
4. Drag issue vào column phù hợp

---

## ✅ Checklist Hoàn Thành

- [ ] Tạo Issue #1 (Authentication)
- [ ] Tạo Issue #2 (Debug files)
- [ ] Tạo Issue #3 (Chart cache)
- [ ] Tạo Issue #4 (Documentation)
- [ ] Tạo Issue #5 (Notebooks)
- [ ] Tạo Issue #6 (Error handlers)
- [ ] Tạo Project Board (optional)
- [ ] Assign issues to yourself
- [ ] Set priorities

---

## 🎯 Tiếp Theo

Sau khi tạo issues:

1. **Bắt đầu với Issue #2** (30 min - nhanh nhất)
   - Xóa debug files
   - Commit & push

2. **Tiếp theo Issue #1** (2-3 hours)
   - Fix authentication
   - Test thoroughly

3. **Cuối cùng Issue #3** (1-2 hours)
   - Fix chart cache
   - Performance testing

---

**Tổng thời gian ước tính:** 5-8 giờ làm việc

Bạn sẵn sàng bắt đầu chưa? 🚀
