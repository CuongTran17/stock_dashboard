# VNStock Dashboard

Ứng dụng theo dõi thị trường chứng khoán Việt Nam, tập trung vào VN30, có dashboard realtime, phân tích kỹ thuật/cơ bản, danh mục cá nhân, thanh toán Premium, Admin dashboard và pipeline ETL đầy đủ.

## Tổng Quan

```text
Frontend Vue 3 + TypeScript + Tailwind CSS + Vite
        |
        | REST API / WebSocket
        v
Backend FastAPI + APScheduler
        |
        +-- MySQL cache/application tables
        +-- Redis tick cache, optional
        +-- Data Lake parquet/raw/processed
        +-- ETL: Extract -> Transform -> Load
```

## Tính Năng

| Nhóm | Mô tả |
|---|---|
| Market dashboard | Bảng giá VN30, market overview, stock screener, chi tiết cổ phiếu |
| Realtime | WebSocket stream VN30, tick cache Redis hoặc fallback in-memory |
| Analysis | Fundamental, financial reports, technical indicators, AI analysis cho Premium |
| Portfolio | Danh mục cá nhân, TP/SL, ghi chú, cảnh báo |
| Premium | Thanh toán nâng cấp qua SePay, promo code, flash sale |
| Admin | Quản lý user, portfolio, doanh thu, khuyến mãi, flash sale |
| ETL Monitor | Theo dõi trạng thái ETL, snapshot, lịch sử chạy, dữ liệu đã extract/transform/load |
| Scheduler | APScheduler cho EOD aggregation, daily ETL, cache refresh, weekly fundamental refresh |

## Tech Stack

**Frontend**

- Vue 3, Composition API
- TypeScript
- Tailwind CSS 4
- Vite 6
- Vue Router 4
- ApexCharts, Lightweight Charts

**Backend**

- FastAPI
- SQLAlchemy
- MySQL 8
- Redis 7, optional
- APScheduler
- vnstock
- pandas, pyarrow/parquet
- GoogleNews, dateparser

## Cài Đặt

### 1. Backend

```powershell
cd C:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend_v2\requirements.txt
```

Tạo và cấu hình `backend_v2\.env`:

```env
MYSQL_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/vnstock_data
JWT_SECRET=change_me_to_a_long_random_string
JWT_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379/0

# ETL
ETL_SYMBOLS=FPT,VCB,VIC
ETL_LOOKBACK_DAYS=365
ETL_TICK_SOURCE=lake
VN30_EOD_JOB_ENABLED=false
VNSTOCK_PRELOAD_REFERENCE_CACHE=true
VNSTOCK_PRELOAD_FORCE_REFRESH=false
VNSTOCK_PRELOAD_SYMBOL_LIMIT=5

# Optional
KAGGLE_API_URL=https://your-kaggle-ngrok.ngrok-free.dev
SEPAY_ENV=sandbox
SEPAY_MERCHANT_ID=your_merchant_id
SEPAY_SECRET_KEY=your_secret
```

Khởi tạo database:

```powershell
mysql -u root -p < backend_v2\init_database.sql
```

### 2. Frontend

```powershell
npm install
```

## Chạy Dự Án

Backend:

```powershell
cd backend_v2
..\.venv\Scripts\python.exe run.py
```

Hoặc từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe backend_v2\run.py
```

Frontend:

```powershell
npm run dev
```

URL mặc định:

- Frontend: `http://localhost:5174`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## ETL Pipeline

Pipeline được tổ chức đúng 3 phần:

### Extract

Nguồn dữ liệu:

- Daily OHLCV theo symbol
- Company overview
- Financial reports
- News/events
- Google News
- Macro indices: VNINDEX, VN30, HNXINDEX, UPCOMINDEX
- Tick/intraday từ Data Lake hoặc Redis khi bật EOD aggregation

Module chính:

- `etl/extract/*`
- `etl/config.py`

### Transform

Các bước xử lý:

- Chuẩn hóa schema cuối pipeline
- Dedup theo symbol/ngày
- Gắn cờ `is_outlier` bằng IQR
- Tính technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, Volume SMA, ATR
- Merge fundamental bằng `merge_asof(direction="backward")` để tránh look-ahead bias
- Gộp và dedup news/event/Google News headline
- Tick to EOD aggregation với session filter

Module chính:

- `etl/transform/build_dataset.py`
- `etl/transform/transform_validate.py`
- `etl/transform/transform_indicators.py`
- `etl/transform/transform_fundamental.py`
- `etl/transform/transform_googlenews.py`
- `etl/transform/transform_aggregate.py`

### Load

Đích ghi dữ liệu:

- `lake/processed/market_data_<run_id>.parquet`
- `lake/processed/market_data_<run_id>.meta.json`
- `lake/processed/by_symbol/<SYMBOL>/latest.parquet`
- `lake/processed/runs/<run_id>.json`
- MySQL:
  - `daily_ohlcv`
  - `company_overview_cache`
  - `financial_report_cache`
  - `news_cache`
  - `events_cache`
  - `technical_cache`

Module chính:

- `etl/load_to_parquet.py`
- `etl/load_to_mysql.py`
- `etl/run_metadata.py`
- `etl/run_etl.py`

## Chạy ETL

Chạy ETL thật cho một mã:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT --start-date 2026-04-20 --end-date 2026-04-28 --output dev-archive\etl_full_fpt.csv --max-workers 2
```

Chạy scheduler độc lập:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler
```

Kiểm tra đăng ký scheduler:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler --dry-run
```

Kiểm tra health ETL:

```powershell
.\.venv\Scripts\python.exe -c "from etl.health import check_etl_health; print(check_etl_health())"
```

## Scheduler

APScheduler có thể chạy embedded trong FastAPI hoặc standalone.

Lịch mặc định:

| Job | Lịch | Mô tả |
|---|---:|---|
| `vn30-eod-job` | 15:15 Mon-Fri | Aggregate tick/intraday thành daily OHLCV, mặc định có thể tắt bằng `VN30_EOD_JOB_ENABLED=false` |
| `etl-daily-full` | 15:20 Mon-Fri | Chạy full ETL |
| `etl-cache-refresh` | 15:30 Mon-Fri | Warmup backend caches sau ETL |
| `etl-weekly-fundamental` | 00:00 Sunday | Refresh dữ liệu fundamental |
| `etl-health-check` | 5 phút/lần | Log cảnh báo nếu dữ liệu stale/error |

## Admin ETL Monitor

Trong Admin dashboard có tab **ETL Monitor**.

Tab này hiển thị:

- Trạng thái health: `healthy`, `stale`, `error`
- Run mới nhất, thời gian chạy, row count, symbols
- Freshness và dung lượng disk
- Mô tả rõ 3 phase Extract, Transform, Load
- Nhóm cột dữ liệu đã được lấy về: identity, price, technical, fundamental, macro, news, quality
- Quality summary: outlier count, duplicate rows, missing columns
- Load targets: parquet, by-symbol parquet, MySQL cache tables
- Lịch sử các ETL runs
- Nút trigger ETL thủ công cho admin, có confirm và rate limit phía backend

## API Endpoints

### Auth

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
PUT  /api/auth/profile
PUT  /api/auth/password
```

### Stocks / Market

```text
GET /api/stocks/vn30
GET /api/stocks/history/{symbol}
GET /api/stocks/intraday/{symbol}
GET /api/market-indices
GET /api/news
WS  /api/ws/market
```

### Analysis

```text
GET  /api/analysis/fundamental/{symbol}
GET  /api/analysis/financial/{symbol}
GET  /api/analysis/technical/{symbol}
POST /api/analysis/ai/{symbol}
```

### Portfolio

```text
GET    /api/portfolio/
POST   /api/portfolio/
PUT    /api/portfolio/{symbol}
DELETE /api/portfolio/{symbol}
```

### Admin

```text
GET    /api/admin/sales-stats
GET    /api/admin/users
PUT    /api/admin/users/{id}/role
PUT    /api/admin/users/{id}/lock
PUT    /api/admin/users/{id}/unlock
GET    /api/admin/promotions
POST   /api/admin/promotions
GET    /api/admin/flash-sales
POST   /api/admin/flash-sales
```

### ETL

```text
GET  /api/etl/status
GET  /api/etl/runs?limit=10
GET  /api/etl/health
POST /api/etl/trigger
```

`POST /api/etl/trigger` yêu cầu admin token và bị rate limit 1 lần mỗi 30 phút.

## Cấu Trúc Dự Án

```text
tailadmin-vuejs-1.0.0/
├── src/
│   ├── views/
│   │   ├── Admin/
│   │   │   ├── AdminDashboard.vue
│   │   │   └── components/
│   │   │       └── TabEtlMonitor.vue
│   │   ├── StockDashboard.vue
│   │   ├── StockDetail.vue
│   │   ├── StockAIAnalysis.vue
│   │   └── ...
│   ├── services/
│   │   ├── authApi.ts
│   │   └── stockBackendApi.ts
│   └── router/
├── backend_v2/
│   ├── src/
│   │   ├── main.py
│   │   ├── jobs.py
│   │   ├── api/
│   │   ├── routes/
│   │   │   └── etl_status.py
│   │   ├── services/
│   │   └── database/
│   ├── init_database.sql
│   └── requirements.txt
├── etl/
│   ├── config.py
│   ├── run_etl.py
│   ├── scheduler.py
│   ├── health.py
│   ├── run_metadata.py
│   ├── load_to_mysql.py
│   ├── load_to_parquet.py
│   ├── extract/
│   └── transform/
├── lake/
│   └── processed/
├── package.json
└── vite.config.ts
```

## Database Tables

| Bảng | Mục đích |
|---|---|
| `daily_ohlcv` | OHLCV ngày |
| `company_overview_cache` | Cache tổng quan doanh nghiệp |
| `financial_report_cache` | Cache báo cáo tài chính |
| `technical_cache` | Cache chỉ báo kỹ thuật |
| `news_cache` | Cache tin tức |
| `events_cache` | Cache sự kiện |
| `users` | Tài khoản |
| `user_subscriptions` | Lịch sử Premium |
| `user_portfolios` | Danh mục cá nhân |
| `ai_predictions` | Kết quả AI |
| `flash_sales` | Flash sale |
| `promo_codes` | Mã khuyến mãi |

## Test Và Verification

Frontend:

```powershell
npm.cmd run type-check
npm.cmd run build-only
```

Backend/ETL compile:

```powershell
.\.venv\Scripts\python.exe -m compileall etl backend_v2\src
```

Kiểm tra route ETL:

```powershell
$env:PYTHONPATH='backend_v2'
.\.venv\Scripts\python.exe -c "from src.main import app; print([r.path for r in app.routes if 'etl' in r.path])"
```

Kết quả mong đợi:

```text
['/api/etl/status', '/api/etl/runs', '/api/etl/health', '/api/etl/trigger']
```

## Production Notes

- Đổi `JWT_SECRET` trước khi deploy.
- Cấu hình CORS theo domain thật, không dùng wildcard trong production.
- Không bật trigger ETL công khai; endpoint đã yêu cầu admin nhưng vẫn nên đặt sau HTTPS/reverse proxy.
- Nên chạy ETL scheduler standalone nếu backend web có thể restart thường xuyên.
- Nên backup `lake/processed` và MySQL cache nếu dùng làm nguồn phục vụ production.
- Với chunk lớn của `apexcharts`, Vite đã tách vendor chunk riêng và đặt warning threshold phù hợp.
