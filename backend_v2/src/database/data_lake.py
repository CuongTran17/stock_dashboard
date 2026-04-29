import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

logger = logging.getLogger(__name__)

_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
DATA_LAKE_DIR = Path(__file__).resolve().parents[2] / "data_lake" / "ticks"


def dump_ticks_to_parquet(symbol: str, ticks: list[dict]):
    if not ticks:
        return

    try:
        today_str = datetime.now(tz=_VN_TZ).strftime("%Y-%m-%d")
        folder_path = DATA_LAKE_DIR / today_str
        folder_path.mkdir(parents=True, exist_ok=True)
        
        file_path = folder_path / f"{symbol}.parquet"
        
        df = pd.DataFrame(ticks)
        if not df.empty:
            df.to_parquet(file_path, engine="pyarrow", index=False)
            logger.info("Dumped %d ticks to Data Lake: %s", len(df), file_path)
    except Exception as exc:
        logger.error("Failed to dump parquet for %s: %s", symbol, exc)
