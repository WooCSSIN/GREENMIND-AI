# Sơ đồ Luồng Vận hành Hệ thống GreenMind (V2 - Logic Optimization)

Sơ đồ này đã được hiệu chỉnh để đảm bảo tính liên kết dữ liệu xuyên suốt và loại bỏ các "nhánh chết" trong hệ thống.

```mermaid
graph TD
    %% Tầng 1: Nguồn Dữ liệu & Giám sát Tức thời
    subgraph Layer_1 [Tầng Dữ liệu & Giám sát CO2]
        A[(Lịch sử Kho & Giá)] --> D[Danh mục Sản phẩm]
        A --> B1[Inventory Emission Engine]
        D --> B1
        B1 -->|Tính toán lãng phí| C[Bảng Nhật ký Cảnh báo ESG]
    end

    %% Tầng 2: Trí tuệ Nhân tạo (Dự báo & Học máy)
    subgraph Layer_2 [AI Engine - Champion Selection]
        A --> E[Feature Engineering & Profiling]
        D --> E
        E --> F{Battle Model Selection}
        F -->|Best MAE| G[SARIMAX]
        F -->|Best Trend| H[Prophet]
        F -->|Non-linear| I[XGBoost]
    end

    %% Tầng 3: Hệ thống Hỗ trợ Ra quyết định (DSS)
    subgraph Layer_3 [Decision Support System - DSS]
        G & H & I --> J[Champion Demand Forecast]
        J --> K[Dynamic Safety Stock SS]
        K --> L[Xác định Reorder Point - ROP]

        %% Note cho công thức
        note1[SS = Z * MAE * sqrt(L)]
    end

    %% Tầng 4: Thực thi & Báo cáo Tác động
    subgraph Layer_4 [Logistics Action & ESG Loop]
        L --> M{Decision Logic}
        M -->|ROP Trigger| N[Logistics Link: Abivin vRoute]
        M -->|Overstock Pulse| O[Tối ưu không gian kho]

        %% Kết nối nhánh chết từ Tầng 1 vào Báo cáo
        C --> P[Hệ thống Báo cáo ESG Tổng hợp]
        J & K --> P
        P --> Q[ISO 14064 Compliance Output]

        %% Feedback Loop
        Q -.->|Cập nhật chính sách tồn kho| Layer_3
    end

    %% Kết nối liên tầng
    Layer_1 ==> Layer_2
    Layer_2 ==> Layer_3
    Layer_3 ==> Layer_4
```

### Các điểm cải tiến Logic quan trọng:

- **Logic Tầng 1:** CO2 không tự nhiên sinh ra. Node `Inventory Emission Engine` sẽ tính toán dựa trên `(Stock - SafetyStock) * EmissionFactor`. Nhật ký ESG (C) giờ đây là bằng chứng thực tế về lãng phí vận hành.
- **Logic Tầng 2:** AI Engine được "nuôi" bởi cả Lịch sử (A) và Danh mục (D). profiling giờ đây bao hàm cả đặc tính SKU và xu hướng mua sắm.
- **Logic Tầng 3 (DSS):** Sử dụng kết quả của mô hình **Champion** (Mô hình tốt nhất trong Battle) để đưa vào công thức tồn kho an toàn. SS (Safety Stock) được tính bằng `Z (Service Level) * MAE (của Champion) * sqrt(Leadtime)`.
- **Logic Tầng 4 (Closed Loop):**
  - Cảnh báo ESG từ Tầng 1 được gom về Báo cáo tổng hợp (P) ở Tầng 4 để đối chiếu với dự báo của AI.
  - **Feedback Loop:** Kết quả báo cáo (Q) sẽ gửi tín hiệu ngược lại Tầng 3 để điều chỉnh Service Level hoặc Lead-time giả định nếu phát thải Carbon đang vượt ngưỡng cho phép của doanh nghiệp.

---

_Bản cập nhật logic v2 - GreenMind AI Architecture | 2026_
