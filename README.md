# VNStock Dashboard

Ứng dụng theo dõi thị trường chứng khoán Việt Nam (VN30) theo thời gian thực, tích hợp phân tích AI, quản lý danh mục đầu tư và thanh toán nâng cấp Premium.

---

## Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + TypeScript + Tailwind CSS 4 + Vite 6)    │
│  Port: 5174                                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API + WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│  Backend (FastAPI 0.116 + Python 3.11+)                     │
│  Port: 8000                                                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  MySQL 8     │  │  Redis 7+    │  │  Data Lake      │   │
│  │  (chính)     │  │  (tùy chọn) │  │  Parquet/EOD    │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tính năng chính

| Tính năng | Mô tả |
|---|---|
| **Thị trường thời gian thực** | WebSocket push dữ liệu tick VN30 mỗi giây |
| **VN30 Dashboard** | Bảng giá tổng quan, lọc/sắp xếp, sparkline |
| **Stock Screener** | Lọc cổ phiếu theo các tiêu chí kỹ thuật |
| **Chi tiết cổ phiếu** | Biểu đồ OHLCV, chỉ số tài chính, tin tức, sự kiện |
| **Phân tích AI** | Tín hiệu BUY/SELL/HOLD từ mô hình Trading-R1 |
| **Danh mục cá nhân** | Watchlist với giá TB, TP, SL, ghi chú |
| **Premium** | Nâng cấp tài khoản qua SePay (QR/chuyển khoản) |
| **Admin Panel** | Quản lý người dùng, xem đơn hàng, khóa tài khoản |
| **EOD Aggregation** | Tự động gộp tick intraday thành nến ngày lúc 15:15 |

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| Redis | 7.0+ (tùy chọn — có fallback in-memory) |

---

## Cài đặt

### 1. Clone dự án

```bash
git clone <repository-url>
cd tailadmin-vuejs-1.0.0
```

### 2. Cài đặt Backend

```bash
cd backend_v2

# Tạo virtual environment
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate
# Kích hoạt (Linux/macOS)
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu hình môi trường Backend

```bash
# Sao chép file cấu hình mẫu
cp .env.example .env
```

Chỉnh sửa `.env` với các giá trị thực:

```env
# ======= MYSQL DATABASE CONFIGURATION =======
MYSQL_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/vnstock_data

# ======= JWT SECURITY =======
JWT_SECRET=change_me_to_a_long_random_string_at_least_32_chars
JWT_EXPIRE_HOURS=24

# ======= VNSTOCK VIP CONFIGURATION ========
VNSTOCK_API_KEY=your_dnse_api_key_here

# ======= SEPAY PAYMENT CONFIGURATION ========
SEPAY_ENV=sandbox
SEPAY_MERCHANT_ID=SP-LIVE-XXXXXXXX
SEPAY_SECRET_KEY=spsk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
SEPAY_BANK_NAME=MB
SEPAY_BANK_ACCOUNT=0123456789
SEPAY_ACCOUNT_NAME=NGUYEN VAN A

# ======= URL CONFIGURATION =======
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8000

# ======= REDIS (tùy chọn) =======
REDIS_URL=redis://localhost:6379/0

# ======= KAGGLE TRADING-R1 AI =======
KAGGLE_API_URL=https://your-kaggle-ngrok.ngrok-free.dev
```

### 4. Khởi tạo Database MySQL

```bash
# Tạo database và các bảng
mysql -u root -p < init_database.sql
```

Hoặc kết nối MySQL thủ công và chạy nội dung file `init_database.sql`.

> **Lưu ý**: Backend sẽ tự động tạo các bảng còn thiếu khi khởi động qua SQLAlchemy `create_all()`, nhưng chạy file SQL đảm bảo đầy đủ index.

### 5. Cài đặt Frontend

```bash
# Quay lại thư mục gốc
cd ..

# Cài đặt Node.js dependencies
npm install
```

---

## Chạy dự án

### Khởi động Backend

```bash
cd backend_v2

# Kích hoạt virtual environment nếu chưa
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/macOS

# Chạy server
python run.py
```

Server chạy tại: `http://localhost:8000`  
API docs (Swagger): `http://localhost:8000/docs`

### Khởi động Frontend

```bash
# Từ thư mục gốc của dự án
npm run dev
```

Ứng dụng chạy tại: `http://localhost:5174`

---

## Cấu trúc dự án

```
tailadmin-vuejs-1.0.0/
├── src/                          # Frontend Vue 3
│   ├── views/
│   │   ├── MarketOverview.vue    # Bảng giá VN30
│   │   ├── StockDashboard.vue    # Dashboard tổng quan
│   │   ├── StockDetail.vue       # Chi tiết cổ phiếu
│   │   ├── StockScreener.vue     # Bộ lọc cổ phiếu
│   │   ├── StockAIAnalysis.vue   # Phân tích AI
│   │   ├── MyPortfolio.vue       # Danh mục cá nhân
│   │   ├── PortfolioAlerts.vue   # Cảnh báo TP/SL
│   │   ├── PremiumUpgrade.vue    # Nâng cấp Premium
│   │   ├── PremiumCheckout.vue   # Thanh toán
│   │   ├── PremiumSePayReturn.vue # Kết quả thanh toán
│   │   ├── Profile.vue           # Thông tin cá nhân
│   │   ├── NewsEvents.vue        # Tin tức & sự kiện
│   │   └── Admin/                # Trang Admin
│   ├── services/
│   │   ├── authApi.ts            # API xác thực
│   │   ├── stockBackendApi.ts    # API dữ liệu cổ phiếu
│   │   ├── dnseApi.ts            # API DNSE
│   │   └── dnseWebSocket.ts      # WebSocket client
│   ├── composables/              # Vue composables
│   ├── components/               # Shared components
│   └── router/                   # Vue Router routes
│
├── backend_v2/
│   ├── src/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── jobs.py               # APScheduler + app lifespan
│   │   ├── utils.py              # Pure helpers
│   │   ├── cache.py              # DB cache helpers
│   │   ├── api/
│   │   │   ├── auth.py           # /api/auth/* (login, register, me)
│   │   │   ├── admin.py          # /api/admin/* (quản lý user)
│   │   │   ├── payment.py        # /api/payment/* (SePay)
│   │   │   └── portfolio.py      # /api/portfolio/* (danh mục)
│   │   ├── routes/
│   │   │   ├── stocks.py         # /api/stocks/* (OHLCV, intraday)
│   │   │   ├── analysis.py       # /api/analysis/* (AI, technical)
│   │   │   ├── market.py         # /api/market-indices/*, /api/news
│   │   │   ├── websocket.py      # /api/ws/market (WebSocket)
│   │   │   └── internal.py       # /api/dnse/*, /api/debug/* (admin only)
│   │   ├── services/
│   │   │   ├── vnstock_fetcher.py   # VN30 intraday fetcher + Redis tick cache
│   │   │   └── fundamental_fetcher.py # Dữ liệu cơ bản, BCTC, kỹ thuật
│   │   └── database/
│   │       ├── db.py             # SQLAlchemy engine + session
│   │       ├── models.py         # ORM models
│   │       ├── redis_db.py       # Redis client (lazy proxy)
│   │       └── data_lake.py      # Parquet EOD dump
│   ├── data_lake/                # Parquet files (tự tạo khi chạy)
│   │   └── ticks/YYYY-MM-DD/SYMBOL.parquet
│   ├── init_database.sql         # Script khởi tạo MySQL
│   ├── requirements.txt
│   ├── run.py                    # Entry point thường
│   └── run_with_ngrok.py         # Entry point cho IPN webhook
└── package.json                  # Frontend dependencies
```

---

## Tài khoản mặc định

| Role | Email | Password |
|---|---|---|
| Admin | `admin@vnstock.vn` | `admin123` |
| Premium | `premium@vnstock.vn` | `premium123` |
| User | `user@vnstock.vn` | `user123` |

> **Bảo mật**: Đổi mật khẩu ngay sau lần đăng nhập đầu tiên ở môi trường production.

---

## API Endpoints chính

### Authentication
```
POST /api/auth/register            Đăng ký tài khoản
POST /api/auth/login               Đăng nhập → JWT token
GET  /api/auth/me                  Thông tin user hiện tại
PUT  /api/auth/profile             Cập nhật hồ sơ
PUT  /api/auth/change-password     Đổi mật khẩu
```

### Dữ liệu thị trường
```
GET  /api/stocks/vn30              Snapshot giá VN30
GET  /api/stocks/intraday/{symbol} Dữ liệu intraday
GET  /api/stocks/history/{symbol}  Lịch sử OHLCV
WS   /api/ws/market                WebSocket stream VN30
```

### Phân tích
```
GET  /api/analysis/fundamental/{symbol}  Dữ liệu cơ bản
GET  /api/analysis/financial/{symbol}    Báo cáo tài chính
GET  /api/analysis/technical/{symbol}    Phân tích kỹ thuật
POST /api/analysis/ai/{symbol}           Phân tích AI (Premium)
```

### Danh mục
```
GET    /api/portfolio/             Danh mục của tôi
POST   /api/portfolio/             Thêm cổ phiếu
PUT    /api/portfolio/{symbol}     Cập nhật
DELETE /api/portfolio/{symbol}     Xóa
```

### Thanh toán Premium
```
POST /api/payment/sepay/create          Tạo đơn thanh toán
GET  /api/payment/sepay/status/{ref}    Kiểm tra trạng thái
POST /api/payment/sepay/webhook         IPN callback từ SePay
```

### Admin
```
GET  /api/admin/users              Danh sách người dùng
PUT  /api/admin/users/{id}/lock    Khóa tài khoản
PUT  /api/admin/users/{id}/unlock  Mở khóa tài khoản
GET  /api/admin/subscriptions      Danh sách đơn hàng
```

---

## Cấu hình nâng cao

### Bật SePay Webhook với ngrok (local dev)

Khi cần test IPN webhook từ SePay trên máy local:

```bash
cd backend_v2

# Cấu hình thêm vào .env:
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
NGROK_DEV_DOMAIN=your-subdomain.ngrok-free.dev
IPN_URL=https://your-subdomain.ngrok-free.dev/api/payment/sepay/webhook

# Chạy với ngrok
python run_with_ngrok.py
```

### Cấu hình preload dữ liệu tham chiếu

```env
# Bật/tắt preload khi khởi động (mặc định: true)
VNSTOCK_PRELOAD_REFERENCE_CACHE=true

# Force refresh dù đã có cache (mặc định: false)
VNSTOCK_PRELOAD_FORCE_REFRESH=false

# Số symbol preload khi khởi động (mặc định: 5, tối đa: 30)
VNSTOCK_PRELOAD_SYMBOL_LIMIT=5
```

### Redis (tùy chọn nhưng khuyến nghị)

Nếu không có Redis, hệ thống tự động dùng fallback in-memory. Tick data sẽ mất khi restart server.

```bash
# Chạy Redis qua Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Cấu trúc database

| Bảng | Mô tả |
|---|---|
| `daily_ohlcv` | Dữ liệu nến ngày OHLCV (được gộp tự động 15:15) |
| `company_overview_cache` | Cache tổng quan doanh nghiệp |
| `financial_report_cache` | Cache báo cáo tài chính |
| `technical_cache` | Cache dữ liệu phân tích kỹ thuật |
| `news_cache` | Cache tin tức theo mã |
| `events_cache` | Cache sự kiện doanh nghiệp |
| `users` | Tài khoản người dùng |
| `user_subscriptions` | Lịch sử thanh toán Premium |
| `user_portfolios` | Danh mục cổ phiếu cá nhân |
| `ai_predictions` | Kết quả phân tích AI |
| `flash_sales` | Chương trình Flash Sale |
| `promo_codes` | Mã chiết khấu |

---

## Tech Stack

**Frontend**
- Vue 3 (Composition API)
- TypeScript
- Tailwind CSS 4
- Vite 6
- Pinia (state management)
- Vue Router 4

**Backend**
- FastAPI 0.116
- SQLAlchemy 2.0 (ORM)
- MySQL 8 (MySQL Connector)
- Redis 7+ (tick cache — optional)
- APScheduler (EOD cron job)
- PyJWT + passlib/bcrypt (auth)
- vnstock 3.5+ (nguồn dữ liệu)
- PyArrow/Parquet (data lake EOD)
- httpx + tenacity (HTTP với retry)

**Payment**
- SePay (QR Banking)

**AI**
- Kaggle Trading-R1 (external API)

---

## Build cho Production

### Frontend

```bash
npm run build
# Output: dist/
```

### Backend

```bash
# Chạy với uvicorn production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> **Lưu ý**: Đặt `allow_origins` trong CORS thành domain cụ thể thay vì `"*"` trong `backend_v2/src/main.py` khi deploy production.
