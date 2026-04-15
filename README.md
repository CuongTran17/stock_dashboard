# VN30 Stock Dashboard (Vue + FastAPI V2)

He thong theo doi VN30 voi:
- Frontend: Vue 3 + TypeScript
- Backend: FastAPI (`backend_v2`) + MySQL
- Du lieu: vnstock (history, intraday, news, events)
- Realtime: WebSocket (`/api/ws/dnse`, `/api/ws/market`)

## Kien truc hien tai

- Backend chinh dang dung: `backend_v2`
- Backend cu khong bi xoa, da duoc dua vao thu muc luu tru: `legacy/`
- Danh sach ma co phieu: chi VN30 (30 ma)
- Du lieu lich su: luu vao MySQL (`daily_ohlcv`)
- Du lieu intraday: cap nhat nen + broadcast realtime
	- Chi goi intraday trong gio giao dich: Thu 2-Thu 6, 09:00-11:30 va 13:00-15:00 (Asia/Ho_Chi_Minh)
- Cuoi phien: gom tick trong ngay thanh OHLCV de ghi DB

## Yeu cau he thong

| Thanh phan | Toi thieu |
|---|---|
| Node.js | 18+ |
| npm | 9+ |
| Python | 3.10+ |
| MySQL | 8+ |

## 1) Cai dat

### Frontend

```powershell
npm install
```

### Backend V2

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend_v2\requirements.txt
```

## 2) Cau hinh backend_v2

File: `backend_v2/.env`

```env
MYSQL_URL=mysql+mysqlconnector://root:your_password@localhost/vnstock_data
VNSTOCK_API_KEY=your_vnstock_api_key

# Tuy chon
VNSTOCK_QUOTE_SOURCE=vci
VNSTOCK_COMPANY_SOURCE=kbs
VNSTOCK_FINANCE_SOURCE=vci
VNSTOCK_MIN_REQUEST_INTERVAL_SECONDS=1.05
VNSTOCK_MAX_REQUESTS_PER_MINUTE=55
VNSTOCK_PRELOAD_SYMBOL_LIMIT=5
VNSTOCK_HISTORY_PRELOAD_SYMBOL_LIMIT=5

# Khuyen nghi voi goi free (60 req/phut)
# Neu van bi vuot quota, giam tiep preload hoac tat preload reference:
# VNSTOCK_PRELOAD_REFERENCE_CACHE=false
```

Khoi tao schema lan dau (tuy chon):

```powershell
.\.venv\Scripts\python.exe backend_v2\test_db.py
```

## 3) Chay du an (2 terminal)

### Terminal 1 - Backend

```powershell
cd backend_v2
..\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 - Frontend

```powershell
	npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend: http://127.0.0.1:5173  
Backend: http://127.0.0.1:8000

## 4) Kiem tra nhanh

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/stocks"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/stocks/snapshots?symbols=FPT,VCB"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/news?symbols=FPT,VCB&limit=10"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/events?symbols=FPT,VCB&limit=10"
```

## 4.1) Tai khoan mau de test role

Neu da chay schema moi (`backend_v2/init_database.sql`), he thong co san 3 tai khoan sau:

| Role | Email | Mat khau |
|---|---|---|
| User | user.sample@stockai.vn | User@123 |
| Premium | premium.sample@stockai.vn | Premium@123 |
| Admin | admin.sample@stockai.vn | Admin@123 |

Tai khoan admin mac dinh:

| Role | Email | Mat khau |
|---|---|---|
| Admin | admin@stockai.vn | admin123 |

Neu DB da tao tu truoc va chua co tai khoan mau, chay lai script SQL:

```powershell
mysql -u root -p vnstock_data < backend_v2\init_database.sql
```

## 5) API chinh

| Method | Endpoint | Mo ta |
|---|---|---|
| GET | `/api/health` | Trang thai backend + DB |
| GET | `/api/stocks` | Danh sach VN30 |
| GET | `/api/stocks/snapshots` | Snapshot realtime cho danh sach ma |
| GET | `/api/stocks/{symbol}/overview` | Tong quan ma |
| GET | `/api/stocks/{symbol}/history` | Lich su gia tu MySQL |
| GET | `/api/stocks/{symbol}/technical` | TA tinh tu du lieu history |
| GET | `/api/stocks/{symbol}/financials` | Stub (chua day du) |
| GET | `/api/market-indices` | Tong hop chi so thi truong |
| GET | `/api/news` | Tin tuc tu `Company.news()` |
| GET | `/api/events` | Su kien tu `Company.events()` |
| POST | `/api/dnse/save-quotes` | Nhan quote realtime tu frontend |

### WebSocket

- `/api/ws/dnse`: route tuong thich frontend hien tai
- `/api/ws/market`: stream cache intraday theo symbol

## 6) TradingView trong trang chi tiet

- Trang `StockDetail` da tich hop chart bang thu vien `TradingView Lightweight Charts`.
- Co dropdown chuyen nhanh giua cac ma VN30 ngay trong trang chi tiet.

## 7) Build production frontend

```powershell
npm run build
```

## 8) Thu muc luu tru ma cu

Code backend cu va script test cu da duoc chuyen vao:

- `legacy/backend_v1`
- `legacy/backend_old`
- `legacy/legacy_tests`

Khong co file nao bi xoa, chi di chuyen de codebase sach hon.

## 9) Xu ly loi thuong gap

PowerShell chan script `.ps1`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Port 8000/5173 dang bi chiem:

```powershell
netstat -ano | findstr LISTENING | findstr ":8000 :5173"
Stop-Process -Id <PID> -Force
```

MySQL ket noi that bai:

- Kiem tra `MYSQL_URL` trong `backend_v2/.env`
- Dam bao DB `vnstock_data` ton tai va user co quyen