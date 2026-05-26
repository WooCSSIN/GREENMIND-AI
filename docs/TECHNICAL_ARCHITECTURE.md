# Kiến trúc Kỹ thuật Hệ thống GreenMind AI

Tài liệu này mô tả cấu trúc dữ liệu và kiến trúc hệ thống của dự án GreenMind AI.

## 1. Sơ đồ Thực thể Quan hệ (ERD)

Sơ đồ này mô tả cách các bảng trong SQL Server kết nối với nhau.

```mermaid
erDiagram
    DIM_USERS ||--o{ FACT_INVENTORY_HISTORY : "Quản lý"
    DIM_PRODUCTS ||--o{ FACT_INVENTORY_HISTORY : "Ghi nhận biến động"
    DIM_PRODUCTS ||--o{ FACT_AI_PREDICTIONS : "Dự báo thông minh"
    DIM_PRODUCTS ||--o{ GREEN_IMPACT_LOGS : "Đánh giá môi trường"

    DIM_PRODUCTS {
        bigint ItemID PK "Mã định danh sản phẩm"
        nvarchar ProductName "Tên hàng hóa"
        nvarchar Category "Phân loại"
        nvarchar Unit "Đơn vị tính"
        float EmissionFactor "Hệ số phát thải CO2"
        int SafetyStockLevel "Mức tồn kho an toàn"
        int ShelfRow "Dãy kệ"
        int ShelfColumn "Cột kệ"
    }

    FACT_INVENTORY_HISTORY {
        int HistoryID PK "ID Giao dịch"
        bigint ItemID FK "Liên kết SKU"
        datetime Timestamp "Thời điểm"
        float Price "Giá"
        float StockQuantity "Số lượng tồn"
        int SoldQuantity "Số lượng bán"
    }

    FACT_AI_PREDICTIONS {
        int PredictionID PK "ID Dự báo"
        bigint ItemID FK "SKU"
        date PredictionDate "Ngày dự báo"
        float ForecastedQuantity "Số lượng dự đoán"
        nvarchar ModelUsed "Mô hình (XGBoost/Prophet)"
    }

    GREEN_IMPACT_LOGS {
        int LogID PK "ID ESG"
        bigint ItemID FK "SKU"
        float AnualCO2Saving "CO2 tiết kiệm"
        float TreesEquivalent "Cây xanh tương đương"
    }
```

## 2. Kiến trúc 3 Tầng (3-Tier Architecture)

Hệ thống được thiết kế theo mô hình phân lớp để đảm bảo tính mở rộng và bảo mật.

### Tầng 1: Data Layer (Lớp Dữ liệu)

- **Công nghệ:** Microsoft SQL Server.
- **Chức năng:** Lưu trữ tập trung dữ liệu Master Data và các bảng Fact. Đảm bảo tính toàn vẹn thông qua Constraints và Triggers.

### Tầng 2: Intelligence Layer (Lớp Trí tuệ AI)

- **Công nghệ:** Python, XGBoost, Scikit-learn, Pandas.
- **Chức năng:**
  - Truy xuất dữ liệu từ SQL thông qua SQLAlchemy.
  - Xử lý đặc trưng (Feature Engineering).
  - Chạy mô hình học máy để đưa ra con số dự báo 30 ngày.

### Tầng 3: Presentation Layer (Lớp Hiển thị)

- **Công nghệ:** Django Framework, Plotly, Tailwind CSS.
- **Chức năng:**
  - Dashboard quản trị Dark Mode.
  - Biểu đồ tương tác thời gian thực.
  - Hệ thống Quản lý Danh mục và Mô phỏng Giao dịch.

---

_Tài liệu này được tạo tự động bởi trợ lý GreenMind AI._
