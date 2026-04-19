"""CLI — **Extract only**: kéo raw data về ``lake/raw/`` (KHÔNG transform).

Tách biệt khỏi transform để khi debug hoặc thay đổi logic chỉ báo, không
phải gọi lại API. Ghi thêm file ``lake/raw/RUN_ID.txt`` để transform sau
biết nên đọc run nào.

Ví dụ:
    python extract_data.py --start-date 2025-04-01 --end-date 2026-04-01 \
        --symbols MBB,FPT,HPG

Output raw:
    lake/raw/prices/<SYMBOL>/<run_id>.csv
    lake/raw/macro_index/<INDEX>/<run_id>.csv
    lake/raw/macro_interbank/<run_id>.json
    lake/raw/overview|ratio_summary|news|events/<SYMBOL>/<run_id>.json
    lake/raw/listing/<run_id>.json
"""
from __future__ import annotations

import argparse

from etl.config import DEFAULT_SYMBOLS, EtlConfig
from etl.logging_setup import get_logger, setup_logging
from etl.run_etl import _check_failure_gate, _extract_all, _parse_symbols

log = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract market raw data -> lake/raw/")
    parser.add_argument("--start-date", default="2025-04-01")
    parser.add_argument("--end-date", default="2026-04-01")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--warmup-days", type=int, default=45)
    parser.add_argument("--lake-dir", default="lake")
    parser.add_argument("--log-dir", default="logs")
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("No valid symbols. Use --symbols MBB,FPT,HPG")

    cfg = EtlConfig.from_args(
        start_date=args.start_date,
        end_date=args.end_date,
        symbols=symbols,
        max_workers=args.max_workers,
        warmup_days=args.warmup_days,
        lake_dir=args.lake_dir,
        log_dir=args.log_dir,
    )
    setup_logging(cfg.log_dir)
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)

    log.info(
        "Extract only: run_id=%s symbols=%d fetch_start=%s end=%s",
        cfg.run_id,
        len(symbols),
        cfg.fetch_start,
        cfg.user_end,
    )
    errors = _extract_all(cfg)
    _check_failure_gate(errors, cfg)

    # Đánh dấu run_id mới nhất để transform_data.py có thể tự lấy.
    latest = cfg.raw_dir / "LATEST_RUN_ID.txt"
    latest.write_text(cfg.run_id, encoding="utf-8")
    log.info("Extract done. run_id=%s marker=%s", cfg.run_id, latest)


if __name__ == "__main__":
    main()
