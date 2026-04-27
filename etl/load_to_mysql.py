import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def get_engine():
    # Load connection string from backend_v2/.env
    env_path = Path("backend_v2/.env")
    if env_path.exists():
        load_dotenv(env_path)
    
    mysql_url = os.getenv("MYSQL_URL")
    if not mysql_url:
        # Fallback to local default if .env is missing
        mysql_url = "mysql+mysqlconnector://root:123456789@localhost/vnstock_data"
        log.warning(f"MYSQL_URL not found in {env_path}, using default: {mysql_url}")
        
    return create_engine(mysql_url)

def load_daily_price():
    """Reads latest Parquet data and upserts into daily_ohlcv table."""
    engine = get_engine()
    
    # 1. Tìm file parquet mới nhất
    parquet_path = Path("lake/processed")
    files = sorted(parquet_path.glob("market_data_*.parquet"))
    if not files:
        log.error("No parquet files found in lake/processed/!")
        return
    
    latest_file = files[-1]
    log.info(f"Loading prices from: {latest_file}")
    
    df = pd.read_parquet(latest_file)
    
    # 2. Xây dựng subset OHLCV
    ohlcv_cols = ['symbol', 'data_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
    
    if not all(col in df.columns for col in ohlcv_cols):
        log.error("Missing required columns in dataset.")
        return
    
    df_ohlcv = df[ohlcv_cols].copy()
    df_ohlcv.rename(columns={
        'data_date': 'date',
        'open_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'close_price': 'close'
    }, inplace=True)
    
    # Đảm bảo volume dạng int (khi fillna có thể nó thành float)
    df_ohlcv['volume'] = df_ohlcv['volume'].fillna(0).astype(int)
    
    records = df_ohlcv.to_dict(orient='records')
    total = len(records)
    
    # 3. UPSERT logic (Insert or Update if symbol+date exists)
    upsert_sql = text("""
        INSERT INTO daily_ohlcv (symbol, date, open, high, low, close, volume)
        VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
        ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume)
    """)
    
    log.info(f"Upserting {total} daily price records to MySQL...")
    
    with engine.begin() as conn:
        conn.execute(upsert_sql, records)
        
    log.info("==> Successfully loaded daily OHLCV to MySQL.")

if __name__ == "__main__":
    load_daily_price()
