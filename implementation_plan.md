# Kế Hoạch Tích Hợp AI-Financial-Analyzer (Trading-R1) & Thiết Kế Kiến Trúc ETL

Bản kế hoạch này mô tả việc thay thế mô hình thống kê ARIMA bằng mô hình Trí tuệ nhân tạo (Trading-R1/Gemma) và tái cấu trúc quy trình ETL cho hệ thống phân tích chứng khoán.

## Đánh giá tính khả thi (Thay ARIMA bằng AI-Financial-Analyzer)
Việc thay thế ARIMA bằng dự án AI-Financial-Analyzer là **hoàn toàn hợp lý, xuất sắc và mang tính đột phá cao cho báo cáo**. 
- **Khuyết điểm của ARIMA:** Là mô hình thống kê truyền thống tuyến tính, cực kì khó dự đoán trước các cú shock đứt gãy của thị trường gây ra bởi tin tức hằng ngày.
- **Sức mạnh của Trading-R1 (FinRL / LLM Agent):** Đưa Mô hình ngôn ngữ lớn kết hợp học tăng cường vào dự án sẽ nâng tầm đồ án từ "Quản lý CSDL kinh điển" sang "Trí tuệ nhân tạo ứng dụng trong Tài chính (Fintech AI)". Mô hình này có thể kết hợp cả dữ liệu số (OHLCV) và dữ liệu chữ (Tin tức, Sự kiện) để đưa ra các lập luận phân tích chi tiết (Reasoning) như một chuyên gia tài chính.

## User Review Required

> [!IMPORTANT]
> **Quyết định về Công nghệ Backend:** Hiện tại bạn có `tailadmin-vuejs-1.0.0` chạy **FastAPI (Python)** tải dữ liệu VNStock, còn `AI-Financial-Analyzer` lại sử dụng backend **Node.js/Express**. \n> \n> Để tối ưu hóa quy trình ETL và báo cáo, tôi cực kỳ khuyến nghị **gộp phần AI vào chung backend Python (FastAPI)**. Vì backend Python có lợi thế tuyệt đối khi chạy các kịch bản Backtrade (`backtest.py`), xử lý Dataframe (Pandas) và giao tiếp thẳng với AI. Bạn có đồng ý gộp hệ thống này theo hướng Python hóa hoàn toàn không?

## Kiến Trúc Quy Trình ETL Cải Tiến
Dưới đây là chi tiết quy trình ETL mà bạn có thể bê trực tiếp vào chương báo cáo của mình.

### 1. Extract (Kéo dữ liệu)
- **Time-series Data:** Kéo dữ liệu giá OHLCV lịch sử và Real-time (Intraday) từ **VNStock / DNSE API** thay vì Yahoo Finance.
- **Unstructured Data:** Kéo tin tức tài chính, sự kiện doanh nghiệp, ngày chia cổ tức.
- **Workflow:** Các jobs (sử dụng `APScheduler`) sẽ được cài đặt để chạy tự động lúc 16:00 mỗi ngày (sau giờ đóng cửa thị trường).

### 2. Transform (Xử lý & Làm sạch)
- **Tính toán Technical Indicators:** Dữ liệu thô lập tức được đẩy qua hàm Python để tính toán RSI, MACD, SMA trong bộ nhớ (Pandas DataFrame).
- **LLM Prompt Engineering:** Đây là bước Transform đặc biệt nhất của dự án AI. Chuyển đổi dữ liệu chuỗi thời gian khô khan thành chuỗi văn bản JSON có cấu trúc để chuẩn bị cho mô hình Trading-R1 thực hiện bước "Reverse Reasoning".
- **Làm sạch:** Loại bỏ các dòng nhiễu, chuẩn hóa thời gian về `ISO 8601`, mapping định dạng của các mốc thời gian lệch múi giờ.

### 3. Load (Lưu trữ và Truyền tải)
- **Database Storage:** Lưu trữ dữ liệu cấu trúc vào MySQL (Các bảng như `CompanyOverviewCache`, `TechnicalCache`, `FinancialReportCache`).
- **AI Inference Pipeline:** Dữ liệu Real-time (đã qua transform) được nén làm Context Payload và đẩy qua Internet tới API của **Colab / Kaggle**, nơi mô hình Trading-R1 đang túc trực phân tích.
- **Data Lake Synchronization:** Kết quả nhận định từ AI trả về sẽ được Load ngược trở lại bảng `AI_Predictions` trong Database MySQL để giữ làm lịch sử Backtest và phục vụ API trực quan hóa lên màn hình VueJS Dashboard.

---

## Proposed Changes (Luồng Triển Khai Vào Code)

### [Backend - FastAPI]
Sử dụng chung backend FastAPI của thư mục VNStock, loại bỏ dần sự phụ thuộc vào Node.js Express.

#### [NEW] `src/services/ai_inference.py`
Tạo file gọi HTTP API (sử dụng thư viện `httpx` hoặc `requests`) bắn payload tới Colab/Kaggle URL thay vì dùng `server.js` của Node.
#### [NEW] `src/scripts/backtest.py`
Di chuyển script backtest từ AI-Analyzer qua đây để chạy kiểm thử win rate trực tiếp trên dữ liệu VNStock được kéo về.
#### [MODIFY] `src/main.py`
Bổ sung các Router API kết nối Frontend UI với module nhận định AI.

### [Database Setup]
#### [MODIFY] `backend_v2/init_database.sql`
Định nghĩa thêm Table `AIPredictions` lưu [Dự đoán, Confidence Score, Ngày tạo, Khuyến nghị Mua/Bán] để tracking lại độ hiệu quả của model.

### [Frontend - VueJS]
#### [NEW] `src/views/TradingAgent.vue`
Thiết kế trang giao diện Dashboard mang hơi hướng Terminal hoặc Chatbot AI, nơi người dùng có thể thấy quá trình model "suy nghĩ" (Reasoning) và cho ra khuyến nghị cổ phiếu hàng ngày.

## Open Questions

> [!WARNING]
> 1. Trở ngại lớp học: Bài báo cáo yêu cầu ARIMA và ETL ở cấp độ "Cơ sở dữ liệu". Khi bạn đổi lên "Mô hình ngôn ngữ lớn (LLM/RL)", tuy công nghệ đỉnh cao hơn nhiều nhưng liệu có bị nhầm sang môn "Trí tuệ nhân tạo" hay "Học máy" và bị giảng viên từ chối không? Bạn đã chốt được định hướng này với Giảng viên chưa?
> 2. Bộ dữ liệu huấn luyện `train_data_mini (6).jsonl` của bạn dường như đang lấy form của sàn Mỹ. Nếu dùng VNStock, chúng ta có cần tạo lại bộ Generator train\_data cho thị trường Việt Nam không?

## Verification Plan

### Automated Tests
- Test pipeline ETL: Kích hoạt chạy thử luồng Ingestion, đảm bảo API ghi dữ liệu mới hằng ngày thành công vào MySQL.
- Backtest Test: Chạy file `backtest.py` cho khoảng 3-5 mã cổ phiếu VN30 ngẫu nhiên với dữ liệu giá trị 1 năm, đảm bảo Sharpe Ratio và Return Rate được tính toán phản ánh chân thực độ hiệu quả của model Trading-R1.

### Manual Verification
- Gửi lệnh gọi mô hình trên Frontend (Ví dụ nhập mã "FPT"), đo đếm thời gian latency request xử lý qua Colab API và trả về, đảm bảo < 15 giây.
