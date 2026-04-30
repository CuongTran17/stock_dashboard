# VNStock Dashboard

Ứng dụng theo dõi thị trường chứng khoán Việt Nam, tập trung vào VN30. Dự án gồm frontend Vue, backend FastAPI, pipeline ETL, data lake parquet và các màn hình vận hành cho admin.

## Tổng Quan

```text
Frontend Vue 3 + TypeScript + Tailwind CSS + Vite
        |
        | REST API / WebSocket
        v
Backend FastAPI + APScheduler
        |
        +-- MySQL: application tables + cache tables
        +-- Redis: optional realtime tick cache
        +-- Data Lake: raw / processed / gold parquet
        +-- ETL: Extract -> Validate/Transform -> Load
```

## Tính Năng

| Nhóm | Mô tả |
|---|---|
| Market dashboard | Bảng giá VN30, market overview, chi tiết cổ phiếu, technical chart |
| Realtime | WebSocket stream, intraday refresh, Redis cache hoặc fallback in-memory |
| Analysis | Fundamental, financial reports, technical indicators, AI analysis qua Kaggle endpoint |
| Portfolio | Danh mục cá nhân, quantity, giá vốn, TP/SL, ghi chú |
| Premium | Thanh toán SePay, promo code, flash sale, subscription status |
| Admin | Quản lý user, portfolio khách hàng, doanh thu, khuyến mãi, flash sale |
| ETL Monitor | Theo dõi health, recent runs, quality summary, load targets, trigger thủ công |
| Scheduler | APScheduler cho ETL, cache warmup, EOD aggregation và health check |
| Observability | `X-Request-ID`, structured error response, liveness/readiness endpoints |

## Tech Stack

**Frontend**

- Vue 3, Composition API
- TypeScript
- Tailwind CSS 4
- Vite 6
- Vue Router 4
- ApexCharts, Lightweight Charts
- Shared HTTP client tại `src/services/httpClient.ts`

**Backend**

- FastAPI, Uvicorn
- SQLAlchemy 2, Alembic
- MySQL 8
- Redis 7, optional
- APScheduler
- pydantic-settings
- vnstock, pandas, pyarrow/parquet
- GoogleNews, dateparser

## Cài Đặt

### 1. Backend

```powershell
cd C:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend_v2\requirements.txt
```

Tạo `backend_v2\.env` từ `backend_v2\.env.example`, rồi cấu hình các biến chính:

```env
# Database
MYSQL_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/vnstock_data
MYSQL_ASYNC_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost/vnstock_data
DB_MIGRATIONS_ENABLED=true
DB_LEGACY_AUTO_DDL=true

# Security / URL
JWT_SECRET=change_me_to_a_long_random_string_at_least_32_chars
JWT_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8000

# Redis optional
REDIS_URL=redis://localhost:6379/0

# ETL runtime
ETL_SYMBOLS=FPT,VCB,VIC
ETL_LOOKBACK_DAYS=365
ETL_TICK_SOURCE=lake
ETL_RUN_MODE=incremental
ETL_INCREMENTAL_OVERLAP_DAYS=7
ETL_CACHE_WARMUP_SCOPE=etl

# Optional integrations
KAGGLE_API_URL=https://your-kaggle-ngrok.ngrok-free.dev
SEPAY_ENV=sandbox
SEPAY_MERCHANT_ID=your_merchant_id
SEPAY_SECRET_KEY=your_secret
```

Khởi tạo database nếu chưa có:

```powershell
mysql -u root -p < backend_v2\init_database.sql
```

Chạy Alembic migrations:

```powershell
cd backend_v2
..\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

Ghi chú:

- Dự án dùng `backend_v2/src/settings.py` làm nguồn cấu hình tập trung.
- App đọc `.env` ở root repo và `backend_v2/.env`; file backend được ưu tiên cho backend runtime.
- Với database local đã tồn tại trước Alembic, app có thể stamp baseline khi startup. Sau khi schema ổn định, nên đặt `DB_LEGACY_AUTO_DDL=false` trong production.

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
- Health: `http://localhost:8000/api/health`

## Backend Runtime

### Settings

Backend không đọc `os.getenv` rải rác trong route/service nữa. Các nhóm cấu hình chính nằm trong `Settings`:

- Database: `MYSQL_URL`, `MYSQL_ASYNC_URL`, migration flags
- Auth: `JWT_SECRET`, `JWT_EXPIRE_HOURS`
- URL/CORS: `FRONTEND_URL`, `BACKEND_URL`, callback URL
- Redis: `REDIS_URL`
- ETL: symbols, lookback, run mode, overlap, warmup scope
- VNStock: source, cache TTL, rate limit, retry, concurrency
- Payment: SePay, premium price/duration
- AI: `KAGGLE_API_URL`

### Observability

Mỗi request có `X-Request-ID`:

- Nếu client gửi header `X-Request-ID`, backend giữ nguyên.
- Nếu không gửi, backend tự sinh request id.
- Response luôn trả lại `X-Request-ID`.
- Log request gồm method, path, status, duration và request id.

Error response giữ `detail` để không phá frontend, đồng thời thêm metadata:

```json
{
  "detail": "Unsupported symbol 'INVALID'. Only VN30 symbols are allowed.",
  "error": {
    "code": "http_error",
    "request_id": "codex-test"
  }
}
```

Các code hiện có:

- `http_error`
- `validation_error`
- `database_error`
- `internal_error`

### Health Endpoints

```text
GET /api/health/live
GET /api/health/ready
GET /api/health
```

`/api/health/live` chỉ kiểm tra process còn sống và không phụ thuộc DB.

`/api/health/ready` kiểm tra:

- MySQL connection
- Alembic version table
- Redis health, optional và có thể ở trạng thái `degraded`

Ví dụ response readiness:

```json
{
  "status": "ok",
  "checked_at": "2026-05-01T00:00:00+00:00",
  "checks": {
    "database": { "status": "ok" },
    "migrations": { "status": "ok", "version": "20260429_0001" },
    "redis": { "status": "degraded", "optional": true }
  }
}
```

Nếu thiếu `alembic_version`, readiness trả `503` với `missing_alembic_version`. Chạy Alembic hoặc để app stamp baseline trên môi trường dev.

## ETL Pipeline

Pipeline được tổ chức theo 3 phần: Extract, Transform, Load.

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
- Validate data quality contract bằng `etl/transform/transform_validate.py`
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
- Gold layer theo partition để phục vụ đọc nhanh
- MySQL cache/application tables:
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

Chạy incremental theo cấu hình mặc định:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB --run-mode incremental --tick-source lake
```

Chạy backfill theo khoảng ngày:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT --start-date 2026-04-20 --end-date 2026-04-28 --run-mode backfill --output dev-archive\etl_full_fpt.csv --max-workers 2
```

Chạy scheduler độc lập:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler
```

Kiểm tra đăng ký scheduler:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler --dry-run
```

Kiểm tra ETL health:

```powershell
.\.venv\Scripts\python.exe -c "from etl.health import check_etl_health; print(check_etl_health())"
```

## Scheduler

APScheduler có thể chạy embedded trong FastAPI hoặc standalone.

Lịch mặc định:

| Job | Lịch | Mô tả |
|---|---:|---|
| `vn30-eod-job` | 15:15 Mon-Fri | Aggregate tick/intraday thành daily OHLCV, mặc định tắt bằng `VN30_EOD_JOB_ENABLED=false` |
| `etl-daily-full` | 15:20 Mon-Fri | Chạy ETL theo cấu hình |
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
- Nhóm cột dữ liệu: identity, price, technical, fundamental, macro, news, quality
- Quality summary: outlier count, duplicate rows, missing columns
- Load targets: parquet, by-symbol parquet, gold layer, MySQL cache tables
- Lịch sử ETL runs
- Nút trigger ETL thủ công cho admin, có confirm và rate limit phía backend

## API Endpoints

### Health

```text
GET /api/health/live
GET /api/health/ready
GET /api/health
```

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
GET /api/stocks
GET /api/stocks/snapshots
GET /api/stocks/{symbol}/overview
GET /api/stocks/{symbol}/history
GET /api/stocks/{symbol}/intraday
GET /api/stocks/{symbol}/ticks
GET /api/stocks/{symbol}/technical
GET /api/stocks/{symbol}/financials
GET /api/market-indices
GET /api/market-indices/{index_symbol}/history
GET /api/news
GET /api/google-news
GET /api/events
WS  /api/ws/market
```

### Analysis

```text
POST /api/analysis/{symbol}/generate
```

### Portfolio

```text
GET    /api/portfolio/
POST   /api/portfolio/
PUT    /api/portfolio/{symbol}
DELETE /api/portfolio/{symbol}
```

### Payment

```text
GET  /api/payment/premium-info
POST /api/payment/create-checkout
GET  /api/payment/subscription-status
POST /api/payment/sepay/webhook
```

### Admin

```text
GET    /api/admin/sales-stats
GET    /api/admin/users
GET    /api/admin/user-portfolios
PUT    /api/admin/users/{user_id}/role
PUT    /api/admin/users/{user_id}/lock
PUT    /api/admin/users/{user_id}/unlock
GET    /api/admin/promotions
POST   /api/admin/promotions
PUT    /api/admin/promotions/{promotion_id}
PATCH  /api/admin/promotions/{promotion_id}/status
DELETE /api/admin/promotions/{promotion_id}
GET    /api/admin/flash-sales
POST   /api/admin/flash-sales
PUT    /api/admin/flash-sales/{flash_sale_id}
PATCH  /api/admin/flash-sales/{flash_sale_id}/status
DELETE /api/admin/flash-sales/{flash_sale_id}
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
│   │   │   └── components/TabEtlMonitor.vue
│   │   ├── StockDashboard.vue
│   │   ├── StockDetail.vue
│   │   └── StockAIAnalysis.vue
│   ├── services/
│   │   ├── httpClient.ts
│   │   ├── authApi.ts
│   │   └── stockBackendApi.ts
│   └── router/
├── backend_v2/
│   ├── alembic/
│   ├── alembic.ini
│   ├── src/
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── api_errors.py
│   │   ├── observability.py
│   │   ├── jobs.py
│   │   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
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
| `alembic_version` | Version schema migration |
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

Backend smoke tests:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend_v2'); from src.main import app; print(app.title)"
```

Kiểm tra health endpoints:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend_v2'); from fastapi.testclient import TestClient; from src.main import app; c=TestClient(app); print(c.get('/api/health/live').json())"
```

Kiểm tra route ETL:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend_v2'); from src.main import app; print([r.path for r in app.routes if 'etl' in r.path])"
```

Kết quả mong đợi:

```text
['/api/etl/status', '/api/etl/runs', '/api/etl/health', '/api/etl/trigger']
```

## Production Notes

- Đổi `JWT_SECRET` trước khi deploy.
- Cấu hình CORS theo domain thật qua `FRONTEND_URL`.
- Chạy Alembic migration trước deploy: `alembic upgrade head`.
- Đặt `DB_LEGACY_AUTO_DDL=false` trong production sau khi migration đã ổn định.
- Theo dõi `/api/health/ready` ở load balancer hoặc container orchestrator.
- Redis là optional, nhưng nên bật nếu chạy nhiều worker hoặc cần sync realtime cache.
- Không public ETL trigger ngoài internet; endpoint đã yêu cầu admin nhưng vẫn nên đặt sau HTTPS/reverse proxy.
- Nên chạy ETL scheduler standalone nếu backend web có thể restart thường xuyên.
- Backup `lake/processed`, gold layer và MySQL nếu dùng làm nguồn phục vụ production.
- Với chunk lớn của `apexcharts`, Vite đã tách vendor chunk riêng và đặt warning threshold phù hợp.
