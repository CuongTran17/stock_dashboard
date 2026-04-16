# Hướng Dẫn Tích Hợp & Chạy Thử Thanh Toán SePay

Tài liệu này hướng dẫn cách thức API thanh toán SePay đang hoạt động trong dự án, cũng như các bước bật hệ thống (Frontend + Backend + Webhook) để test chức năng nâng cấp Premium tại máy cá nhân.

---

## 1. Kiến Trúc Luồng Thanh Toán (SePay IPN Flow)

1. **Frontend (Vue.js):** 
   - Người dùng đăng nhập, truy cập `/premium/checkout` và ấn nút "Thanh toán SePay".
   - Vue gọi API `POST /api/payment/create-checkout` của Backend FastAPI.
2. **Backend (FastAPI):**
   - Sinh ra mã `order_invoice_number` và `order_description` (Chứa `user_id`).
   - Cấu tạo chuỗi cấu hình (gồm danh sách các url, số tiền).
   - Mã hóa HMAC-SHA256 để sinh ra biến `signature` hợp lệ theo đúng thuật toán mà SDK Node.js yêu cầu.
3. **SePay Gateway:**
   - Frontend nhận cấu hình từ Backend, tự động chèn vào Form ẩn và chuyển hướng (Submit POST) sang cổng `https://sandbox.pay.sepay.vn/v1/checkout/init` hoặc cổng Live.
   - Khi thanh toán thành công (hoặc hủy), SePay đẩy người dùng về `FRONTEND_URL/premium/sepay-return?status=...`.
4. **IPN Webhook (quan trọng):**
   - Cùng lúc đó, hệ thống máy chủ của SePay sẽ gọi API chạy ngầm xuống: `POST /api/payment/sepay/webhook` (thông qua đường dẫn ngrok).
   - Ở đây, Backend tra mã `user_id`, cập nhật vai trò người dùng thành "premium", và lưu lịch sử vào DB `user_subscriptions`.

---

## 2. Chuẩn Bị File `.env` (Backend)

Trong quá trình test ở localhost, bạn **bắt buộc phải sử dụng mã Sandbox** thay vì Live để SePay không chặn các URL trả về `http://localhost`. Cấu hình trong `backend_v2/.env` nên như sau:

```env
SEPAY_ENV=sandbox

# API Key lấy trên trang quản trị SePay (Môi trường Test)
SEPAY_MERCHANT_ID=SP-TEST-TD54A554
SEPAY_SECRET_KEY=spsk_test_41D8f24AyGBisC86uHtT4F8zEDvRHUF8

# URL Frontend đang chạy, chú ý thay đổi Port nếu bị nhảy
FRONTEND_URL=http://localhost:5174
FRONTEND_CALLBACK_URL=http://localhost:5174
```

---

## 3. Các Bước Bật Hệ Thống Chi Tiết Môi Trường Test

Để thực hiện Test thành công, bạn buộc phải mở cho SePay chui vào được Webhook ở máy cá nhân (thông qua Ngrok).

### Bước 3.1: Chạy Frontend (Vue3)
Tại thư mục gốc của dự án:
```bash
npm install
npm run dev
```
> **Lưu ý:** Xem kỹ log hiện ra để biết web đang chạy ở `http://localhost:5173` hay `http://localhost:5174`. Sau đó đối chiếu vào `.env` của Backend để sửa lại nếu bị lệch port.

### Bước 3.2: Khởi động Backend + Ngrok
Để Backend vừa chạy API cục bộ vừa lắng nghe được IPN của SePay bắn vào, dự án đã chuẩn bị sẵn file `run_with_ngrok.py`. Tại thư mục `backend_v2/`:
```bash
# Bật môi trường ảo (Windows)
.venv\Scripts\activate

# Cài requirements (nếu chưa có)
pip install -r requirements.txt

# Bật hệ thống backend
python run_with_ngrok.py
```
Script `run_with_ngrok.py` sẽ tự động:
- Bật FastAPI Server ở `port 8000`.
- Chạy hầm kết nối Ngrok tại port 8000.
- Kết nối thông suốt public domain ngrok vào biến môi trường `IPN_URL` (Ví dụ `https://xxxxx.ngrok.dev/api/payment/sepay/webhook`) và sử dụng nó lúc thanh toán!

### Bước 3.3: Thao Tác Thanh Toán (SePay Sandbox)
1. Đăng nhập Frontend `localhost:517x`.
2. Vào trang Nâng cấp Premium -> Click "Thanh toán qua SePay".
3. Trình duyệt nhảy sang cổng Test của SePay. Tại đây, chọn ngân hàng bất kỳ, điện thoại có thể quét mã giả (hoặc lấy mã số thanh toán ở dưới nhấn hoàn thành giả lập).
4. Quan sát log trên cửa sổ Terminal của backend. Nếu thấy dòng tin:
   `[Sepay IPN] Received webhook...`
   `✅ SUCCESS: User ... upgraded to premium...`
   -> Nghĩa là hệ thống đã nhận IPN, user đã được nâng cấp.
5. Về lại màn hình Vue -> Chờ giao diện tự check Status 5 giây sau hiển thị thông báo nâng cấp thành công 🎉.

---

## 4. Chuyển Đổi Sang Môi Trường Thật (Production)

Khi bạn muốn đưa sản phẩm công khai cho người dùng trả tiền thực:
1. Sửa `.env` từ Sandbox thành cặp khóa **LIVE**: `SEPAY_MERCHANT_ID=SP-LIVE-...` và `SEPAY_SECRET_KEY=spsk_live...`
2. Đổi `FRONTEND_URL` và `FRONTEND_CALLBACK_URL` sang Domain thật (VD: `https://stock.cua-ban.com`).
3. Đổi `IPN_URL` thành Backend trên Server thật: `https://api.cua-ban.com/api/payment/sepay/webhook`. (Lúc này không cần chạy Ngrok nữa).
