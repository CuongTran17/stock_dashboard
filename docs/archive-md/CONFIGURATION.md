# Backend Configuration Guide

## VNStock Data Source Configuration

### Recommended Settings for Free-Tier (60 requests/minute)

```bash
# Company API - Use KBS (Web Scraping - Most Stable)
VNSTOCK_COMPANY_SOURCE=kbs

# Financial API - Use VCI (Default & Recommended for detailed data)
VNSTOCK_FINANCE_SOURCE=vci

# Financial Period
VNSTOCK_FINANCIAL_PERIOD=quarter

# Rate Limiting
VNSTOCK_MAX_REQUESTS_PER_MINUTE=55

# Startup Preload Optimization
VNSTOCK_PRELOAD_REFERENCE_CACHE=true
VNSTOCK_PRELOAD_SYMBOL_LIMIT=5
VNSTOCK_HISTORY_PRELOAD_SYMBOL_LIMIT=5
VNSTOCK_HISTORY_PRELOAD_CONCURRENCY=1
```

## Source Comparison

### Company API (Company Overview, News, Events)
- **KBS**: Recommended ✅
  - 30 columns
  - Web scraping (no quota impact)
  - Stable response format
- VCI: Not recommended ⚠️
  - Only 10 columns
  - Inconsistent response shape

### Financial API (Income Statement, Balance Sheet, Ratios)
- **VCI**: Recommended ✅
  - Most detailed (37+ ratios)
  - Long-form format (period × metric)
  - Supports note/commentary
  - Automatic retry on connection errors
- KBS: Alternative
  - Wide-form format (metric × period)
  - 27 ratios

## Startup Flow

1. **Initialize MySQL schema** - Create tables with idempotent checks
2. **Start intraday fetch loop** - Poll VN30 ticks during trading hours
3. **Preload historical data** - Load 365 days for first 5 symbols (configurable)
4. **Preload reference caches** - Load company overview + financials for first 5 symbols

## Error Handling & Resilience

### Connection Error Retry Logic
Financial API calls automatically retry with exponential backoff on connection errors:
- **Max attempts**: 3 (configurable in code)
- **Backoff**: 1s → 2s → 4s (exponential, capped at 10s)
- **Errors caught**: ConnectionError, TimeoutError, HTTPError, URLError, etc.
- **Fallback**: Returns cached data if fresh fetch fails after all retries

Example flow:
```
Attempt 1: ConnectionError → Wait 1s, retry
Attempt 2: ConnectionError → Wait 2s, retry
Attempt 3: ConnectionError → Log warning, return cached data or empty
```

### Rate Limit Handling
- Global rate limiter: 55 requests/minute (headroom on 60 req/min free tier)
- Intraday requests: Smart retry with extracted `retry_after` duration
- Financial requests: Retry with exponential backoff on connection errors

## Troubleshooting

### Connection Errors in Financial Reports

**Symptom:**
```
WARNING:src.services.fundamental_fetcher:refresh_financial_report failed for ACB (ratios): RetryError[<Future...state=finished raised ConnectionError>]
```

**Cause:**
- Network timeout or temporary connection failure
- VCI financial endpoint not responding

**Solution:**
- Backend automatically retries with exponential backoff (up to 3 attempts)
- If all retries fail, endpoint returns cached data or empty list
- Wait a moment and refresh - next attempt may succeed
- Check if vnstock servers are accessible: ping `api.vietstock.vn` or check VNStock status

### "provider payload unavailable" Errors

**Symptom:**
```
INFO:src.services.fundamental_fetcher:refresh_company_overview provider payload unavailable for ACB
```

**Solution:**
- Verify `VNSTOCK_COMPANY_SOURCE=kbs` is set
- This error only occurs with VCI and indicates inconsistent response format
- Backend handles gracefully with retry and fallback logic

### Rate Limit Errors

**Symptom:**
```
WARNING:src.services.vnstock_fetcher:refresh_symbol_intraday rate-limited for VCI. Retrying in 21.0s
```

**Solution:**
- Reduce `VNSTOCK_PRELOAD_SYMBOL_LIMIT` (default: 5)
- Reduce `VNSTOCK_HISTORY_PRELOAD_CONCURRENCY` (default: 1)
- Wait for rate limit window to pass
- Consider upgrading to premium vnstock tier

## Environment Variables Reference

### Data Sources
- `VNSTOCK_COMPANY_SOURCE` - "kbs" (recommended) or "vci"
- `VNSTOCK_QUOTE_SOURCE` - "vci" (default, for intraday/history)

### SePay Checkout
- `SEPAY_ENV` - "sandbox" or "production"
- `SEPAY_MERCHANT_ID` - Merchant ID do SePay cap
- `SEPAY_SECRET_KEY` - Secret key do SePay cap
- `SEPAY_BANK_NAME` - Ma ngan hang nhan tien, vi du `MB`
- `SEPAY_BANK_ACCOUNT` - So tai khoan nhan tien
- `SEPAY_ACCOUNT_NAME` - Ten chu tai khoan
- `FRONTEND_URL` - URL frontend de quay ve trang checkout/return
- `BACKEND_URL` - URL backend chinh
- `SEPAY_IPN_URL` - URL IPN SePay se go ve backend
- `IPN_URL` - Alias runtime cho `SEPAY_IPN_URL`, dung khi script ngrok inject tu dong

### ngrok Local IPN
- `IPN_PORT` - Cong chay IPN/ngrok local (mac dinh 3001)
- `NGROK_AUTHTOKEN` - Authtoken cua ngrok dashboard
- `NGROK_DEV_DOMAIN` - Domain ngrok da reserve de nhan IPN local

### Preload Configuration
- `VNSTOCK_PRELOAD_REFERENCE_CACHE` - Enable/disable company data preload (default: true)
- `VNSTOCK_PRELOAD_FORCE_REFRESH` - Force refresh on startup (default: false)
- `VNSTOCK_PRELOAD_SYMBOL_LIMIT` - Number of symbols to preload (default: 5)
- `VNSTOCK_HISTORY_PRELOAD_SYMBOL_LIMIT` - History symbols to preload (default: 5)
- `VNSTOCK_HISTORY_PRELOAD_CONCURRENCY` - Parallel history workers (default: 1)

### Rate Limiting
- `VNSTOCK_MAX_REQUESTS_PER_MINUTE` - Global rate limit (default: 55 for 60/min free tier)

### Cache TTL
- `VNSTOCK_NEWS_CACHE_TTL_SECONDS` - News cache duration (default: 300s)
- `VNSTOCK_EVENTS_CACHE_TTL_SECONDS` - Events cache (default: 900s)
- `VNSTOCK_OVERVIEW_CACHE_TTL_SECONDS` - Overview cache (default: 21600s)
- `VNSTOCK_FINANCIAL_CACHE_TTL_SECONDS` - Financial cache (default: 21600s)
