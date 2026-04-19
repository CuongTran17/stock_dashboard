# PROJECT DOCUMENTATION (UNIFIED)

Tai lieu nay la ban hop nhat de su dung du an. Muc tieu la thay cho viec doc roi rac nhieu file .md.

## 1. Du an nay la gi

VN30 Stock Dashboard gom:
- Frontend: Vue 3 + TypeScript + Vite
- Backend chinh: FastAPI trong `backend_v2`
- Du lieu: vnstock (history, intraday, overview, news, events)
- Realtime: WebSocket (`/api/ws/dnse`, `/api/ws/market`)
- Payment: SePay checkout + IPN webhook
- ETL: bo script cu + huong tach ETL module hoa trong thu muc `etl/`

## 2. Folder nao chuc nang nao

| Folder/File | Chuc nang |
|---|---|
| `src/` | Frontend Vue (views, components, services, router) |
| `public/` | Tai nguyen static cho frontend |
| `backend_v2/` | Backend FastAPI chinh dang su dung |
| `backend_v2/src/routes/` | Dinh nghia API routes |
| `backend_v2/src/services/` | Nghiep vu lay du lieu vnstock, cache, processing |
| `backend_v2/src/database/` | Ket noi DB, model, init schema |
| `backend_v2/init_database.sql` | SQL khoi tao bang va seed user mau |
| `etl/` | ETL module hoa (extract/transform/config/retry/logging) |
| `lake/raw/` | Du lieu raw cho ETL |
| `lake/processed/` | Du lieu da xu ly cho model/phan tich |
| `legacy/backend_v1/` | Backend cu da luu tru |
| `legacy/backend_old/` | Mot phien ban backend cu hon da luu tru |
| `legacy/legacy_tests/` | Script test cu da chuyen vao luu tru |
| `vnstock-agent-guide/` | Bo tai lieu tham khao va huong dan AI agent cho he sinh thai vnstock |
| `docs/PROJECT_DOCUMENTATION.md` | Tai lieu chinh (file nay) |

## 3. Yeu cau he thong

- Node.js 18+
- npm 9+
- Python 3.10+
- MySQL 8+
- (Tuỳ chon) ngrok cho webhook/payment

## 4. Cai dat

### 4.1 Frontend

```powershell
npm install
```

### 4.2 Backend

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend_v2\requirements.txt
```

## 5. Cau hinh backend (`backend_v2/.env`)

Gia tri toi thieu:

```env
MYSQL_URL=mysql+mysqlconnector://root:your_password@localhost/vnstock_data
VNSTOCK_API_KEY=your_vnstock_api_key
```

Gia tri de on dinh voi free-tier vnstock:

```env
VNSTOCK_COMPANY_SOURCE=kbs
VNSTOCK_FINANCE_SOURCE=vci
VNSTOCK_QUOTE_SOURCE=vci
VNSTOCK_MAX_REQUESTS_PER_MINUTE=55
VNSTOCK_PRELOAD_REFERENCE_CACHE=true
VNSTOCK_PRELOAD_SYMBOL_LIMIT=5
VNSTOCK_HISTORY_PRELOAD_SYMBOL_LIMIT=5
VNSTOCK_HISTORY_PRELOAD_CONCURRENCY=1
```

## 6. Chay du an

### Cach nhanh (khuyen nghi)

Terminal 1 - Backend + ngrok:

```powershell
npm run backend:ngrok
```

Terminal 2 - Frontend:

```powershell
npm run dev
```

Mac dinh frontend chay o `http://localhost:5174` (strictPort theo package.json).

### Cach backend thu cong (khong ngrok)

```powershell
.\.venv\Scripts\python.exe backend_v2\run.py
```

## 7. Kiem tra nhanh API

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/stocks"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/stocks/snapshots?symbols=FPT,VCB"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/news?symbols=FPT,VCB&limit=10"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/events?symbols=FPT,VCB&limit=10"
```

## 8. Tai khoan mau de test role

Neu da chay `backend_v2/init_database.sql`, co san:

- user.sample@stockai.vn / User@123
- premium.sample@stockai.vn / Premium@123
- admin.sample@stockai.vn / Admin@123

## 9. Payment SePay (tom tat)

Flow:
1. Frontend goi `POST /api/payment/create-checkout`
2. Redirect sang SePay checkout
3. SePay goi webhook `POST /api/payment/sepay/webhook`
4. Backend cap nhat premium + lich su subscription

Bien moi truong chinh:

```env
SEPAY_ENV=sandbox
SEPAY_MERCHANT_ID=SP-TEST-...
SEPAY_SECRET_KEY=spsk_test_...
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8000
SEPAY_IPN_URL=https://<ngrok-domain>/api/payment/sepay/webhook
```

## 10. ETL va data pipeline

### 10.1 Hien trang

- Script ETL cu o root: `extract_data.py`, `transform_data.py`, `generate_market_data.py`, `fetch_interbank_rate.py`
- ETL module hoa o `etl/`:
  - `etl/extract/*`: lay du lieu
  - `etl/transform/*`: tinh toan va lam sach
  - `etl/retry.py`: retry policy
  - `etl/logging_setup.py`: logging tap trung
  - `etl/run_etl.py`: orchestrator

### 10.2 Nguyen tac ETL khuyen nghi

- Tach E-T-L ro rang
- Khong dung backfill (`bfill`) cho chuoi macro de tranh look-ahead bias
- Co warm-up window cho RSI/MACD/EMA
- Co retry + logging + data quality gate
- Du lieu raw luu o `lake/raw`, output luu o `lake/processed`

## 11. API chinh

| Method | Endpoint | Mo ta |
|---|---|---|
| GET | `/api/health` | Health backend + DB |
| GET | `/api/stocks` | Danh sach VN30 |
| GET | `/api/stocks/snapshots` | Snapshot nhieu ma |
| GET | `/api/stocks/{symbol}/overview` | Thong tin doanh nghiep |
| GET | `/api/stocks/{symbol}/history` | Lich su gia |
| GET | `/api/stocks/{symbol}/technical` | Chi bao ky thuat |
| GET | `/api/news` | Tin tuc thi truong |
| GET | `/api/events` | Su kien thi truong |
| POST | `/api/dnse/save-quotes` | Luu quote realtime |
| WS | `/api/ws/dnse` | WS route tuong thich frontend |
| WS | `/api/ws/market` | Stream market cache |

## 12. Thu muc legacy

Tat ca code cu duoc giu, khong xoa:
- `legacy/backend_v1`
- `legacy/backend_old`
- `legacy/legacy_tests`
- `legacy/archive-code` (script/ma nguon khong con nam trong luong runtime chinh)
- `legacy/archive-artifacts` (artifact trung gian, file trich xuat thu cong, du lieu tam)

Khuyen nghi: khong them tinh nang moi vao legacy, chi doc/doi chieu.

## 13. Tai lieu da duoc hop nhat vao file nay

Noi dung thuc thi da duoc tong hop tu:
- `README.md`
- `docs/archive-md/CONFIGURATION.md`
- `docs/archive-md/SEPAY_GUIDE.md`
- `docs/archive-md/ETL_IMPROVEMENT_ROADMAP.md`
- `docs/archive-md/implementation_plan.md`

Cac file tren van duoc giu lai de trace lich su va phuc vu doi chieu.

## 14. Tai lieu tham khao khong thuoc core app

- `vnstock-agent-guide/` la bo tai lieu huong dan chung cho he sinh thai vnstock/AI agents.
- Day la tai lieu thu vien/agent reference, khong phai luong van hanh chinh cua app nay.
