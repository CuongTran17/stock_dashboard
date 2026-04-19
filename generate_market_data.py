"""Thin CLI wrapper — chạy toàn bộ pipeline E -> T -> L qua module ``etl``.

File này giữ giao diện CLI cũ để các script/PIPE đang dùng vẫn hoạt động:
    python generate_market_data.py --start-date 2025-04-01 --end-date 2026-04-01 \
        --symbols MBB,FPT,HPG --output market_data.csv --text-mode dense

Toàn bộ logic nằm trong package ``etl/``:
    - etl/extract/*   : fetch & dump raw vào lake/raw/
    - etl/transform/* : đọc raw, tính indicator, ghép dataset sạch (ffill-only)
    - etl/run_etl.py  : orchestrator (ThreadPool + retry + fail-ratio gate)

Nếu cần chạy riêng 2 pha, dùng ``extract_data.py`` và ``transform_data.py``.
"""
from __future__ import annotations

import argparse

from etl.config import DEFAULT_SYMBOLS, EtlConfig
from etl.run_etl import _parse_symbols, run

DEFAULT_START_DATE = "2025-04-01"
DEFAULT_END_DATE = "2026-04-01"
DEFAULT_OUTPUT_FILE = "market_data.csv"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate market_data.csv via etl package (Extract -> Transform -> Load)",
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="End date in YYYY-MM-DD")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Output CSV path")
    parser.add_argument(
        "--symbols",
        default=",".join(DEFAULT_SYMBOLS),
        help="Comma-separated stock symbols, e.g. MBB,FPT,HPG",
    )
    parser.add_argument(
        "--text-mode",
        default="dense",
        choices=["dense", "raw"],
        help="dense: fill headline gaps forward only, raw: keep only true daily news/events",
    )
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--warmup-days", type=int, default=45)
    parser.add_argument("--lake-dir", default="lake")
    parser.add_argument("--log-dir", default="logs")
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("No valid symbols provided. Use --symbols, e.g. --symbols MBB,FPT,HPG")

    cfg = EtlConfig.from_args(
        start_date=args.start_date,
        end_date=args.end_date,
        symbols=symbols,
        text_mode=args.text_mode,
        output_file=args.output,
        max_workers=args.max_workers,
        warmup_days=args.warmup_days,
        lake_dir=args.lake_dir,
        log_dir=args.log_dir,
    )

    output_path = run(cfg)
    print(f"Generated: {output_path.resolve()}")


if __name__ == "__main__":
    main()
