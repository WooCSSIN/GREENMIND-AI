# 🌿 GreenMind AI: Enterprise Green Logistics WMS

GreenMind là nền tảng quản trị kho thông minh tự thích nghi, được thiết kế chuyên biệt cho Logistics Xanh tại Việt Nam. Hệ thống kết hợp sức mạnh của Django (Web), SQL Server (Data), và AI Multi-model (Engine) để tối ưu hóa tồn kho và giảm thiểu dấu chân Carbon.

---

## 🏗️ Cấu trúc dự án (Standard DEV Structure)

Dự án được tổ chức theo chuẩn công nghiệp để đảm bảo tính bảo mật và khả năng bảo trì:

- 📂 `apps/`: Chứa các ứng dụng Django chức năng (`api`, `dashboard`).
- 📂 `core/`: Cấu hình hệ thống (Settings, URL routing, Middleware, Throttling).
- 📂 `engine/`: Lõi xử lý AI chuyên sâu (SARIMAX, Prophet, XGBoost) và Logic nghiệp vụ.
- 📂 `database/`: Các kịch bản SQL Server (Table, Stored Procedures, Triggers).
- 📂 `scripts/`: Các công cụ quản trị (Worker tự động, Health Check, RBAC Setup).
- 📂 `docs/`: Tài liệu kỹ thuật, báo cáo bảo mật và hướng dẫn triển khai.
- 📂 `static/` & `core/templates/`: Giao diện người dùng (Tailwind CSS, Dark Mode).

---

## 🚀 Tính năng cốt lõi

- **AI Multi-Model Battle:** Tự động chọn mô hình dự báo nhu cầu chính xác nhất cho từng SKU.
- **Green Metrics & ESG:** Tính toán lượng phát thải CO2 tiết kiệm và quy đổi ra cây xanh tuong đương.
- **Audit Trail & RBAC:** Phân quyền người dùng (Admin, Manager, Viewer) và ghi nhật ký thao tác bảo mật.
- **Warehouse Heatmap:** Giám sát trực quan mật độ tồn kho theo vị trí kệ hàng.
- **Production Ready:** Hệ thống đã được Hardening với HSTS, SSL Redirect, Rate Limiting, và Error Sanitization.

---

## 🛠️ Hướng dẫn cài đặt

### 1. Cơ sở dữ liệu (SQL Server)

Chạy các script trong thư mục `database/` theo thứ tự:

1. `Create_table.sql`
2. `migration_v3_security.sql` (Ràng buộc an toàn dữ liệu)
3. `TRIGGERS.sql` (Logic tính toán CO2)
4. `TRASACTION.sql` (Giao dịch nhập/xuất kho)

### 2. Môi trường Python

```bash
python -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

### 3. Cấu hình & Chạy

1. Tạo file `.env` từ `.env.example`.
2. Kiểm tra sức khỏe hệ thống: `python scripts/health_check.py`.
3. Khởi chạy Server: `python manage.py runserver`.
4. (Tùy chọn) Chạy Worker AI: `python scripts/worker.py`.

---

## 👥 Đội ngũ phát triển

- **Project Lead:** Hà Nhật Nguyên Vũ
- **Data Scientist:** Nguyễn Văn Tới
- **Logistics Expert:** Nguyễn Đào Kiều Dung
- **Environmental Specialist:** Lê Huỳnh Quang Minh

---

_GreenMind AI Core Platform | Enterprise Edition v2.0 | 2026_
