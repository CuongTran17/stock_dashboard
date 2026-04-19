"""CLI — **Transform only**: đọc ``lake/raw/`` và xuất ``market_data.csv``.

Không gọi API. Dùng cho trường hợp đã chạy ``extract_data.py`` xong và chỉ
cần tính lại indicator / đổi text_mode.

Mặc định, script lấy ``run_id`` từ ``lake/raw/LATEST_RUN_ID.txt`` (được
``extract_data.py`` ghi ra). Có thể ghi đè bằng ``--run-id``.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from etl.config import DEFAULT_SYMBOLS, EtlConfig
from etl.logging_setup import get_logger, setup_logging
from etl.run_etl import _parse_symbols
from etl.transform.build_dataset import build_full_dataset, validate_dataset

log = get_logger(__name__)


def _resolve_run_id(lake_dir: Path, override: str | None) -> str:
    if override:
        return override
    marker = lake_dir / "raw" / "LATEST_RUN_ID.txt"
    if not marker.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {marker}. Chạy extract_data.py trước hoặc truyền --run-id."
        )
    return marker.read_text(encoding="utf-8").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform raw -> market_data.csv")
    parser.add_argument("--start-date", default="2025-04-01")
    parser.add_argument("--end-date", default="2026-04-01")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--text-mode", default="dense", choices=["dense", "raw"])
    parser.add_argument("--output", default="market_data.csv")
    parser.add_argument("--lake-dir", default="lake")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--warmup-days", type=int, default=45)
    parser.add_argument("--run-id", default=None, help="Run ID của extract đã chạy; mặc định đọc LATEST_RUN_ID.txt")
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("No valid symbols. Use --symbols MBB,FPT,HPG")

    lake_dir = Path(args.lake_dir)
    run_id = _resolve_run_id(lake_dir, args.run_id)

    # Build config rồi ghi đè run_id.
    cfg = EtlConfig.from_args(
        start_date=args.start_date,
        end_date=args.end_date,
        symbols=symbols,
        text_mode=args.text_mode,
        output_file=args.output,
        warmup_days=args.warmup_days,
        lake_dir=args.lake_dir,
        log_dir=args.log_dir,
    )
    # ``EtlConfig`` là frozen -> dùng dataclasses.replace thay vì gán trực tiếp.
    from dataclasses import replace
    cfg = replace(cfg, run_id=run_id)

    setup_logging(cfg.log_dir)
    log.info(
        "Transform only: run_id=%s symbols=%d user_range=%s..%s text_mode=%s",
        cfg.run_id,
        len(symbols),
        cfg.user_start,
        cfg.user_end,
        cfg.text_mode,
    )

    dataset = build_full_dataset(cfg.symbols, cfg)
    if dataset.empty:
        raise RuntimeError("Empty dataset — kiểm tra lake/raw có đủ file không.")
    validate_dataset(dataset)

    cfg.output_file.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(
        cfg.output_file,
        index=False,
        encoding="utf-8-sig",
        float_format="%.6f",
    )

    snapshot = cfg.processed_dir / f"market_data_{cfg.run_id}.csv"
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(cfg.output_file, snapshot)

    log.info(
        "Done: %s rows=%d range=%s..%s symbols=%s",
        cfg.output_file,
        len(dataset),
        dataset["data_date"].min(),
        dataset["data_date"].max(),
        ",".join(sorted(dataset["symbol"].unique().tolist())),
    )


if __name__ == "__main__":
    main()
