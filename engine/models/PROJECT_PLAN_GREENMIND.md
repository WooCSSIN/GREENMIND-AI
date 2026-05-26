# Kế hoạch Triển khai Dự án Nghiên cứu Khoa học: GREENMIND

**Đề tài:** Hệ sinh thái Quản lý Chuỗi cung ứng & Thương mại điện tử Xanh (Green Supply Chain & E-commerce Eco-system)
**Mục tiêu:** Tối ưu hóa vận hành logistics, giảm thiểu lãng phí và đo lường tác động môi trường dựa trên dữ liệu thực tế và AI.

---

## Giai đoạn 1: Xây dựng Nền tảng Dữ liệu (Data Foundation) - [Đang thực hiện]

**Mục tiêu:** Chuẩn bị "nguyên liệu" sạch để chứng minh tính cấp thiết của đề tài và huấn luyện mô hình AI.

- **1.1. Thu thập dữ liệu:**
  - [x] Có dataset mẫu: `Shopee_Products_Master.csv`.
  - [ ] (Mở rộng) Cân nhắc crawl thêm dữ liệu từ các sàn khác (Lazada, Tiki) hoặc sử dụng bộ dữ liệu học thuật mở rộng (Kaggle) về hành vi mua sắm để tăng độ tin cậy.
- **1.2. Làm sạch & Chuẩn hóa (Data Cleaning Pipeline):**
  - [x] Xử lý lỗi font, định dạng ngày tháng.
  - [x] Tách bảng Master (Danh mục) và History (Biến động).
  - [x] Xử lý số liệu (Discount, Price, Stock).
  - **Kết quả:** Bộ dữ liệu sạch sẵn sàng cho AI (`Optimized/`).

## Giai đoạn 2: Phát triển Lõi Thông minh (AI Core Intelligence) - [Bước kế tiếp]

**Mục tiêu:** Xây dựng các mô hình dự báo để giải quyết bài toán "Tối ưu nguồn lực".

- **2.1. Mô hình Dự báo Nhu cầu (Demand Forecasting):**
  - _Input:_ `Price_Stock_History.csv` (Chuỗi thời gian: Lượng bán, Giá, Khuyến mãi).
  - _Thuật toán:_ ARIMA, Prophet (Facebook), hoặc LSTM (Deep Learning).
  - _Output:_ Dự đoán số lượng hàng cần nhập trong tuần/tháng tới.
  - _Giá trị xanh:_ Giảm tồn kho chết (Dead stock) -> Giảm lãng phí tài nguyên & điện năng kho bãi.
- **2.2. Phân tích Vòng đời sản phẩm:**
  - Xác định khi nào sản phẩm đi vào giai đoạn thoái trào (dựa trên trạng thái `sold_out` lâu dài hoặc `banned`).
  - Đề xuất chiến lược xả hàng hoặc thu hồi/tái chế.

## Giai đoạn 3: Xây dựng Hệ thống GreenWMS (Warehouse Management System)

**Mục tiêu:** Hiện thực hóa giải pháp phần mềm quản lý kho thông minh.

- **3.1. Thiết kế Cơ sở dữ liệu (Database Schema):**
  - Tích hợp bảng `Products`, `Inventory` với các bảng "Xanh": `Energy_Consumption` (Tiêu thụ năng lượng), `Carbon_Footprint` (Dấu chân Carbon).
- **3.2. Tính năng Lõi:**
  - Quản lý Nhập/Xuất/Tồn.
  - **Green Dashboard:** Hiển thị chỉ số phát thải CO2 cho mỗi đơn hàng (tính toán dựa trên quãng đường vận chuyển và bao bì đóng gói).
  - Tích hợp IoT (giả lập): Theo dõi nhiệt độ/độ ẩm kho để bảo quản hàng hóa tối ưu (giảm hỏng hóc).

## Giai đoạn 4: Đánh giá & Viết Báo cáo NCKH

**Mục tiêu:** Hoàn thiện hồ sơ dự thi và bài báo khoa học.

- **4.1. Đánh giá Hiệu quả (Evaluation):**
  - So sánh mô hình GreenWMS với mô hình truyền thống (Ví dụ: Giảm được bao nhiêu % tồn kho dư thừa dựa trên dự báo của AI?).
  - Dựa trên data Shopee đã xử lý để chạy mô phỏng (Simulation).
- **4.2. Viết báo cáo:**
  - Chương 1: Tổng quan & Lý thuyết (Green Supply Chain, Circular Economy).
  - Chương 2: Phương pháp nghiên cứu & Dữ liệu (Mô tả quy trình xử lý data Shopee).
  - Chương 3: Xây dựng hệ thống (Kiến trúc GreenWMS, AI Model).
  - Chương 4: Kết quả thực nghiệm & Kết luận.

---

## Đề xuất hành động ngay lập tức (Next Actions)

1.  **Chốt mô hình AI:** Bạn muốn dùng thuật toán đơn giản (như Moving Average) hay phức tạp (Machine Learning) cho phần dự báo? Tôi có thể viết code demo dự báo nhu cầu dựa trên file `Price_Stock_History.csv`.
2.  **Thiết kế Database:** Bắt đầu vẽ sơ đồ ERD cho hệ thống GreenWMS, trong đó trọng tâm là các bảng dữ liệu môi trường.
