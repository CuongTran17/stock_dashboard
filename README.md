# VNStock Dashboard

Ứng dụng theo dõi và phân tích thị trường chứng khoán Việt Nam, tập trung vào dữ liệu VN30. Dự án gồm frontend Vue 3, backend FastAPI, pipeline ETL, data lake Parquet, DuckDB warehouse và các màn hình vận hành cho admin.

## Tổng Quan Kiến Trúc

```text
Vue 3 + TypeScript + Vite
        |
        | REST API / một WebSocket dùng chung
        v
FastAPI backend
        |
        +-- MySQL: user, auth, portfolio, payment, cache nghiệp vụ
        +-- DuckDB: daily OHLCV, technical cache, market feature mart
        +-- Redis: optional realtime/cache runtime
        +-- lake/: raw, processed, gold parquet snapshots
        +-- etl/: Extract -> Transform -> Load
```

## Thành Phần Chính

| Thành phần | Mô tả |
|---|---|
| Frontend | Dashboard, danh mục, phân tích cổ phiếu, realtime price store dùng chung, admin, ETL monitor |
| Backend | API FastAPI, auth JWT, payment SePay, portfolio, stock/market endpoints |
| ETL | Lấy dữ liệu giá, chỉ số, tin tức, cơ bản, transform indicator và load snapshot |
| Data lake | Lưu raw/processed/gold Parquet để tái lập snapshot |
| DuckDB | Kho dữ liệu market local cho OHLCV, technical cache và feature mart |
| MySQL | Dữ liệu app/user/business và một số cache nghiệp vụ |
| Redis | Tùy chọn, dùng cho realtime/cache; nếu không có backend có fallback in-memory |

## Yêu Cầu Môi Trường

- Node.js 22 hoặc tương thích với Vite 6.
- Python 3.11+.
- MySQL 8 local hoặc remote.
- Redis 7 là tùy chọn.
- Windows PowerShell được dùng trong các ví dụ bên dưới.

## Cài Đặt Lần Đầu

### 1. Cài frontend dependencies

```powershell
cd C:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0
npm install
```

### 2. Tạo Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend_v2\requirements.txt
```

### 3. Tạo file môi trường backend

Copy file mẫu:

```powershell
Copy-Item backend_v2\.env.example backend_v2\.env
```

Các biến cần kiểm tra trong `backend_v2\.env`:

```env
MYSQL_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/vnstock_data
MYSQL_ASYNC_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost/vnstock_data
DUCKDB_PATH=lake/warehouse/market.duckdb

JWT_SECRET=change_me_to_a_long_random_string_at_least_32_chars
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8000

REDIS_URL=redis://localhost:6379/0

ETL_SYMBOLS=FPT,VCB,VIC
ETL_LOOKBACK_DAYS=365
ETL_TICK_SOURCE=lake
ETL_RUN_MODE=incremental
ETL_INCREMENTAL_OVERLAP_DAYS=7

VNSTOCK_API_KEY=your_dnse_api_key_here
KAGGLE_API_URL=https://your-kaggle-ngrok.ngrok-free.dev

DNSE_MARKET_BASE_URL=https://openapi.dnse.com.vn
DNSE_MARKET_API_KEY=your_dnse_openapi_key
DNSE_MARKET_API_SECRET=your_dnse_openapi_secret
DNSE_MARKET_BOARD_ID=G1
DNSE_TICK_POLL_INTERVAL_MS=2000
DNSE_TICK_PARQUET_FLUSH_SECONDS=30
DNSE_REALTIME_POLL_WHEN_CLOSED=false
DNSE_REALTIME_CLOSED_HEARTBEAT_SECONDS=300

MARKET_TIMEZONE=Asia/Ho_Chi_Minh
MARKET_MORNING_START=09:00
MARKET_MORNING_END=11:30
MARKET_AFTERNOON_START=13:00
MARKET_AFTERNOON_END=14:45
MARKET_CLOSE_END=15:00
```

Ghi chú:

- Backend đọc cấu hình từ `.env` ở root repo và `backend_v2\.env`; file trong `backend_v2` phù hợp nhất cho runtime backend.
- Frontend dev server đã có proxy `/api` sang `http://127.0.0.1:8000`, nên thường không bắt buộc tạo `.env.local`.
- Nếu muốn frontend gọi backend bằng URL tuyệt đối, tạo `.env.local` ở root:

```env
VITE_BACKEND_URL=http://127.0.0.1:8000
VITE_BACKEND_POLLING_MS=15000
```

Frontend tự ưu tiên WebSocket và chuyển sang polling snapshot khi kết nối realtime không khả dụng. `VITE_BACKEND_POLLING_MS` điều chỉnh chu kỳ polling fallback.

### 4. Khởi tạo MySQL database

Tạo database và bảng nền tảng:

```powershell
mysql -u root -p < backend_v2\init_database.sql
```

Chạy migration:

```powershell
cd backend_v2
..\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
cd ..
```

### 5. Tạo dữ liệu market snapshot ban đầu

Backend đang theo hướng strict snapshot: API đọc dữ liệu snapshot có sẵn, không tự fetch dữ liệu thị trường khi startup. Vì vậy sau khi cài đặt nên chạy ETL ít nhất một lần.

Chạy nhanh vài mã để kiểm tra pipeline:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB --run-mode incremental --tick-source lake --max-workers 2
```

Chạy toàn bộ VN30 theo mặc định:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --run-mode incremental --tick-source lake
```

Kết quả ETL chính:

- `market_data.csv`
- `market_data.parquet`
- `lake\raw\...`
- `lake\processed\market_data_<run_id>.parquet`
- `lake\processed\runs\<run_id>.json`
- `lake\silver\market_data\run_id=<run_id>\data.parquet`
- `lake\silver\market_data\latest.parquet`
- `lake\gold\market_features\latest.parquet`
- `lake\manifests\latest_success.json`
- `lake\warehouse\market.duckdb`

## Các Bước Khi Khởi Động Dự Án

Làm theo checklist này mỗi lần mở dự án local:

1. Mở terminal tại root repo:

```powershell
cd C:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0
```

2. Kích hoạt Python environment:

```powershell
.\.venv\Scripts\activate
```

3. Đảm bảo MySQL đang chạy và `backend_v2\.env` trỏ đúng `MYSQL_URL`.

4. Nếu dùng Redis, bật Redis:

```powershell
cd backend_v2
docker compose up -d redis
cd ..
```

Nếu không dùng Redis, backend vẫn có thể chạy với fallback in-memory cho một số luồng.

5. Chạy migration khi vừa pull code mới hoặc schema thay đổi:

```powershell
cd backend_v2
..\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
cd ..
```

6. Kiểm tra hoặc cập nhật snapshot market nếu dữ liệu cũ:

```powershell
.\.venv\Scripts\python.exe -c "from etl.health import check_etl_health; print(check_etl_health())"
```

Nếu health báo stale/missing, chạy ETL:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --run-mode incremental --tick-source lake
```

7. Chạy backend:

```powershell
.\.venv\Scripts\python.exe backend_v2\run.py
```

8. Mở terminal khác và chạy frontend:

```powershell
npm run dev
```

9. Truy cập:

- Frontend: `http://localhost:5174`
- Backend Swagger: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/health`
- Readiness: `http://localhost:8000/api/health/ready`

## Cách Chạy Backend

Từ root repo:

```powershell
.\.venv\Scripts\python.exe backend_v2\run.py
```

Hoặc từ thư mục backend:

```powershell
cd backend_v2
..\.venv\Scripts\python.exe run.py
```

Backend mặc định chạy tại `http://localhost:8000`.

Chạy backend kèm ngrok cho webhook SePay local:

```powershell
npm run backend:ngrok
```

Trước khi dùng ngrok, cấu hình các biến `NGROK_AUTHTOKEN`, `NGROK_DEV_DOMAIN`, `IPN_URL` hoặc `SEPAY_IPN_URL` trong `backend_v2\.env`.

## Cách Chạy Frontend

```powershell
npm run dev
```

Các script frontend:

| Lệnh | Mô tả |
|---|---|
| `npm run dev` | Chạy Vite dev server port 5174 |
| `npm run build` | Type-check và build production |
| `npm run build-only` | Chỉ build Vite |
| `npm run type-check` | Kiểm tra TypeScript/Vue |
| `npm run test:unit` | Chạy unit test một lần bằng Vitest |
| `npm run test:unit:watch` | Chạy Vitest ở watch mode |
| `npm run lint` | Chạy ESLint và tự fix |
| `npm run preview` | Preview bản build |

## Realtime Giá Cổ Phiếu Trên Frontend

Frontend quản lý giá hiện tại bằng một luồng realtime tập trung, thay vì để từng trang tự mở WebSocket hoặc tự polling:

```text
App.vue
  └── realtimeManager
        ├── WebSocket /api/ws/market
        ├── polling fallback /api/stocks/snapshots
        ├── symbolRegistry
        └── stockPriceStore
              └── các trang đọc cùng một nguồn giá
```

- `App.vue` khởi động và dừng duy nhất một `realtimeManager` theo vòng đời ứng dụng.
- Mỗi trang dùng `usePriceSubscription(ownerId, symbols)` để khai báo các mã đang cần.
- `symbolRegistry` gộp và đếm số nơi đang dùng từng mã; mã chỉ bị bỏ đăng ký khi không còn trang nào cần.
- Quote từ WebSocket được ghi ngay vào `stockPriceStore`. Khi WebSocket lỗi, manager polling snapshot cho các mã đang active và tự thử kết nối lại.
- Watchlist của người dùng và danh sách mã đang xem realtime là hai khái niệm riêng biệt.
- Chỉ giá hiện tại tự cập nhật không cần reload trang. Lịch sử giá, technical, tin tức, sự kiện, tài chính và AI analysis vẫn giữ cách refresh hiện tại.

Các trang đang dùng luồng giá tập trung gồm Dashboard, Stock Detail, My Portfolio, Portfolio Alerts, Stock Screener và News Events. Xem mô tả chi tiết tại `docs/frontend-realtime-architecture.md`.

## Cách Chạy ETL

ETL entrypoint chính là:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl
```

### Chạy incremental

Incremental tự tìm snapshot mới nhất trong `lake\processed`, lùi lại một số ngày overlap rồi merge vào snapshot hiện tại.

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB,VIC --run-mode incremental --incremental-overlap-days 7 --tick-source lake
```

### Chạy full theo khoảng ngày

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB,VIC --start-date 2025-04-01 --end-date 2026-04-01 --run-mode full
```

### Chạy backfill một khoảng ngày

Backfill phù hợp khi cần cập nhật lại một đoạn dữ liệu trong snapshot hiện có.

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT --start-date 2026-04-20 --end-date 2026-04-28 --run-mode backfill --max-workers 2
```

### Chạy nhanh khi chỉ cần giá và technical

Tắt bớt nguồn nặng như fundamental hoặc Google News:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB --run-mode incremental --disable-fundamental --disable-google-news --max-workers 2
```

### Chỉ ghi file, bỏ qua MySQL hoặc DuckDB

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --symbols FPT,VCB --disable-mysql-load --disable-duckdb-market-load
```

### Các tham số ETL hay dùng

| Tham số | Mô tả |
|---|---|
| `--symbols FPT,VCB` | Danh sách mã, phân tách bằng dấu phẩy |
| `--start-date YYYY-MM-DD` | Ngày bắt đầu output |
| `--end-date YYYY-MM-DD` | Ngày kết thúc output |
| `--run-mode full` | Chạy lại toàn bộ khoảng ngày được chỉ định |
| `--run-mode incremental` | Cập nhật dựa trên snapshot mới nhất |
| `--run-mode backfill` | Ghi đè/merge một khoảng ngày vào snapshot mới nhất |
| `--incremental-overlap-days 7` | Số ngày overlap khi incremental |
| `--max-workers 6` | Số worker extract song song |
| `--tick-source lake` | Nguồn tick để aggregate EOD: `lake`, `redis`, `auto` |
| `--disable-fundamental` | Không extract báo cáo tài chính |
| `--disable-google-news` | Không extract Google News |
| `--disable-mysql-load` | Không load cache vào MySQL |
| `--disable-duckdb-market-load` | Không load market warehouse vào DuckDB |
| `--no-merge-with-latest` | Không merge incremental/backfill với snapshot mới nhất |

## Data Lake Publish Model

ETL ghi immutable run artifacts truoc, sau do moi publish snapshot cho app doc. Mot run chi duoc xem la serving-ready khi:

1. Transform tao dataset thanh cong.
2. Final merged dataset vuot qua publish quality gate.
3. Processed, silver, gold va DuckDB/MySQL load hoan tat.
4. `lake\manifests\latest_success.json` duoc cap nhat atomic.

Mo hinh nay giup tranh tinh huong mot snapshot loi bi app doc nham la latest. Khi quality gate fail, run metadata se ghi `failed`, nhung manifest latest cu van duoc giu nguyen.

Current compatible paths:

| Layer/path | Vai tro |
|---|---|
| `lake\raw` | Raw extractor files theo source/run |
| `lake\processed` | Legacy processed snapshots, giu de tuong thich script cu |
| `lake\silver\market_data` | Normalized market data theo `run_id` va `latest.parquet` |
| `lake\gold\market_features` | Feature mart cho AI/backtest/API |
| `lake\manifests\latest_success.json` | Serving pointer cho snapshot thanh cong moi nhat |
| `lake\warehouse\market.duckdb` | Local analytical warehouse va AI job/result store |

Quality gate hien check cac loi schema/duplicate/OHLC/volume/close, symbol coverage va outlier ratio. Mac dinh yeu cau it nhat 95% so ma ky vong co mat trong dataset va outlier ratio khong qua 5%.

## Scheduler ETL

Kiểm tra các job sẽ đăng ký:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler --dry-run
```

Chạy scheduler độc lập:

```powershell
.\.venv\Scripts\python.exe -m etl.scheduler
```

Lịch mặc định:

| Job | Lịch | Mô tả |
|---|---:|---|
| `etl-daily-full` | 15:20 Mon-Fri | Chạy ETL incremental |
| `etl-cache-refresh` | 15:30 Mon-Fri | Refresh cache sau ETL |
| `etl-weekly-fundamental` | 00:00 Sunday | Refresh dữ liệu cơ bản |
| `etl-health-check` | 5 phút/lần | Kiểm tra freshness và lỗi ETL |

Backend web hiện không nên được xem là nơi tự động tạo snapshot market khi startup. Đường ghi dữ liệu market được khuyến nghị là CLI ETL, scheduler độc lập hoặc admin ETL trigger.

## DuckDB Và Market Feature Mart

Đường dẫn mặc định:

```text
lake/warehouse/market.duckdb
```

Inspect mart:

```powershell
.\.venv\Scripts\python.exe -m etl.inspect_duckdb_market_mart
```

Backfill mart từ Parquet snapshot:

```powershell
.\.venv\Scripts\python.exe -m etl.backfill_duckdb_market_features --parquet lake/gold/market_features/latest.parquet --run-id backfill-latest
```

Backfill kết quả thực tế cho các lần phân tích AI:

```powershell
.\.venv\Scripts\python.exe -m etl.backfill_ai_prediction_outcomes --horizon-trading-days 5
```

### AI Analysis Ledger Trong DuckDB

Ket qua AI duoc luu trong cung DuckDB warehouse:

```text
lake/warehouse/market.duckdb
```

Backend se tao schema DuckDB khi startup. Sau khi co thay doi schema moi, nen restart backend de cac bang moi nhu `ai_generation_jobs` duoc tao bang `CREATE TABLE IF NOT EXISTS`.

Bang chinh:

| Bang | Noi dung |
|---|---|
| `ai_generation_jobs` | Trang thai job async: `queued`, `running`, `success`, `failed` |
| `ai_analysis_runs` | Metadata cua moi lan phan tich: symbol, status, decision, confidence, model version, error |
| `ai_analysis_payloads` | Input/output day du: context, prompt, Kaggle response, raw model output, normalized output |
| `ai_prediction_outcomes` | Ket qua doi chieu sau nay cho backtest/evaluation |

Mapping input/output trong `ai_analysis_payloads`:

| Cot | Y nghia |
|---|---|
| `request_context_json` | Market context dua vao model |
| `prompt_text` | Prompt thuc te gui sang Trading-R1/Kaggle API |
| `kaggle_response_json` | JSON response tu API |
| `raw_output` | Raw text output cua model |
| `normalized_output_json` | Ket qua da parse/normalize de frontend hien thi |

Inspect nhanh so dong:

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; c=duckdb.connect('lake/warehouse/market.duckdb', read_only=True); print(c.execute('SELECT COUNT(*) FROM ai_analysis_runs').fetchone()); print(c.execute('SELECT COUNT(*) FROM ai_analysis_payloads').fetchone()); print(c.execute('SELECT COUNT(*) FROM ai_generation_jobs').fetchone())"
```

Xem 5 lan phan tich moi nhat:

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; c=duckdb.connect('lake/warehouse/market.duckdb', read_only=True); print(c.execute('SELECT analysis_id, symbol, status, decision, confidence, created_at, completed_at FROM ai_analysis_runs ORDER BY created_at DESC LIMIT 5').fetchall())"
```

## Admin ETL Monitor

Trong Admin Dashboard có tab ETL Monitor để xem:

- ETL health và freshness.
- Run gần nhất, số dòng, số mã, thời gian chạy.
- Quality summary.
- Load targets: Parquet, gold layer, DuckDB, MySQL cache.
- Lịch sử các run.
- Nút trigger ETL thủ công cho admin.

Endpoint ETL:

```text
GET  /api/etl/status
GET  /api/etl/runs?limit=10
GET  /api/etl/health
POST /api/etl/trigger
```

`POST /api/etl/trigger` yêu cầu admin token và có rate limit.

## API Chính

Health:

```text
GET /api/health/live
GET /api/health/ready
GET /api/health
```

Auth:

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
PUT  /api/auth/profile
PUT  /api/auth/password
```

Stocks/Market:

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

DNSE tick sandbox:

```text
GET /api/dnse/ticks/status
GET /api/dnse/ticks/latest?symbols=FPT,VCB,VIC
GET /api/dnse/ticks/debug?symbol=FPT
```

Trang test frontend:

```text
http://localhost:5174/dnse-ticks
```

Trang nay chi dung de test latest trade/tick read-only tu DNSE. Neu chua cau hinh `DNSE_MARKET_API_KEY` va `DNSE_MARKET_API_SECRET`, backend se tra `not_configured` de frontend hien thi loi cau hinh ro rang.

Backend co market-hours guard cho DNSE realtime:

- Trong phien `09:00-11:30`, `13:00-14:45`, va phien ATC/closing den `15:00`: `/api/dnse/ticks/latest` poll DNSE binh thuong.
- Tick hop le duoc giu trong Redis hoac in-memory fallback va duoc flush atomic xuong `backend_v2/data_lake/ticks/YYYY-MM-DD/{symbol}.parquet` theo chu ky `DNSE_TICK_PARQUET_FLUSH_SECONDS`.
- Ngoai phien, nghi trua, hoac cuoi tuan: endpoint khong poll DNSE nua ma doc last-known tick theo thu tu cache -> Parquet. Response giu `status=market_closed`, them `is_stale=true`, `data_source=cached_last_tick`, `missing_symbols`, kem `market_session` va `next_open_at`.
- Frontend sandbox van hien tick da luu neu co, kem canh bao stale mau vang va giam nhip heartbeat theo `DNSE_REALTIME_CLOSED_HEARTBEAT_SECONDS`.
- Neu chay local khong co Redis, cac tick trong in-memory co the mat sau backend restart neu chua kip flush Parquet.
- Neu can test DNSE ngoai phien, dung `/api/dnse/ticks/debug?symbol=FPT` hoac tam thoi set `DNSE_REALTIME_POLL_WHEN_CLOSED=true`.
- Guard nay giup tranh viec gia cu tu DNSE bi hien thi nhu realtime tick moi.

Analysis:

```text
POST /api/analysis/{symbol}/generate
```

Portfolio:

```text
GET    /api/portfolio/
POST   /api/portfolio/
PUT    /api/portfolio/{symbol}
DELETE /api/portfolio/{symbol}
```

Payment:

```text
GET  /api/payment/premium-info
POST /api/payment/create-checkout
GET  /api/payment/subscription-status
POST /api/payment/sepay/webhook
```

Admin:

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

## Cấu Trúc Thư Mục

```text
tailadmin-vuejs-1.0.0/
├── src/                         # Frontend Vue
│   ├── views/
│   ├── components/
│   ├── composables/             # usePriceSubscription, useStockData
│   ├── realtime/                # manager và registry symbol
│   ├── services/
│   ├── stores/                  # shared current-price store
│   ├── test/                    # Vitest setup
│   └── router/
├── backend_v2/                  # FastAPI backend
│   ├── alembic/
│   ├── src/
│   │   ├── api/
│   │   ├── routes/
│   │   ├── services/
│   │   └── database/
│   ├── init_database.sql
│   ├── requirements.txt
│   └── run.py
├── etl/                         # ETL pipeline
│   ├── extract/
│   ├── transform/
│   ├── run_etl.py
│   ├── scheduler.py
│   └── load_to_duckdb.py
├── lake/                        # Data lake local
│   ├── raw/
│   ├── processed/
│   ├── gold/
│   └── warehouse/
├── logs/
├── package.json
└── vite.config.ts
```

## Kiểm Tra Và Build

Frontend:

```powershell
npm run test:unit
npm run type-check
npm run build-only
```

Unit test realtime frontend bao phủ registry symbol, cập nhật shared price store, lifecycle/fallback của realtime manager và DNSE WebSocket service.

Backend/ETL compile:

```powershell
.\.venv\Scripts\python.exe -m compileall etl backend_v2\src
```

Backend smoke test:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend_v2'); from src.main import app; print(app.title)"
```

Health smoke test:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend_v2'); from fastapi.testclient import TestClient; from src.main import app; c=TestClient(app); print(c.get('/api/health/live').json())"
```

## Lỗi Thường Gặp

### Frontend gọi API không được

- Đảm bảo backend đang chạy ở `http://localhost:8000`.
- Nếu dùng `VITE_BACKEND_URL`, kiểm tra file `.env.local`.
- Nếu không dùng `VITE_BACKEND_URL`, Vite dev proxy sẽ chuyển `/api` sang backend.

### Backend báo lỗi database

- Kiểm tra MySQL đang chạy.
- Kiểm tra `MYSQL_URL` và `MYSQL_ASYNC_URL`.
- Chạy lại migration:

```powershell
cd backend_v2
..\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
cd ..
```

### API market báo không có snapshot

Chạy ETL để tạo snapshot:

```powershell
.\.venv\Scripts\python.exe -m etl.run_etl --run-mode incremental --tick-source lake
```

### ETL bị chậm

- Giảm số mã bằng `--symbols`.
- Tắt nguồn nặng bằng `--disable-fundamental --disable-google-news`.
- Giảm worker nếu bị rate limit: `--max-workers 2`.

### Redis không chạy

Redis là optional cho local dev. Nếu muốn bật:

```powershell
cd backend_v2
docker compose up -d redis
cd ..
```

## Ghi Chú Production

- Đổi `JWT_SECRET` trước khi deploy.
- Cấu hình CORS bằng `FRONTEND_URL`.
- Chạy Alembic migration trước khi deploy.
- Sau khi schema ổn định, cân nhắc đặt `DB_LEGACY_AUTO_DDL=false`.
- Không public admin ETL trigger trực tiếp ngoài internet.
- Backup `lake\processed`, `lake\gold`, `lake\warehouse` và MySQL.
- Chạy ETL scheduler như process riêng nếu cần cập nhật dữ liệu định kỳ.
