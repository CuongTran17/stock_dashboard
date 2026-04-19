"""Orchestrator — chạy Extract song song rồi Transform tuần tự.

Pipeline:
    1. setup_logging() + tạo lake/raw, lake/processed.
    2. Extract song song qua ThreadPoolExecutor:
         - listing (1 lần)
         - macro_index x 4 chỉ số
         - macro_interbank (1 lần)
         - per symbol: prices, overview, ratio_summary, news, events
       Mỗi job có tenacity retry riêng. Job thất bại -> log + đếm vào failed.
    3. Gate: nếu tỉ lệ mã lỗi > cfg.max_fail_ratio -> raise.
    4. Transform: đọc raw, tính indicator, ghép dataset sạch.
    5. Ghi ra cfg.output_file + copy snapshot vào lake/processed/.

CLI::

    python -m etl.run_etl --start-date 2025-04-01 --end-date 2026-04-01 \
        --symbols MBB,FPT,HPG --output market_data.csv
"""
from __future__ import annotations

import argparse
import logging
import shutil
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Callable

from etl.config import DEFAULT_SYMBOLS, MACRO_SYMBOLS, EtlConfig
from etl.extract.extract_company import (
    extract_events,
    extract_listing,
    extract_news,
    extract_overview,
    extract_ratio_summary,
)
from etl.extract.extract_interbank import extract_interbank_rate
from etl.extract.extract_prices import extract_index_prices, extract_symbol_prices
from etl.logging_setup import get_logger, setup_logging
from etl.transform.build_dataset import build_full_dataset, validate_dataset

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Job scheduling helpers
# ---------------------------------------------------------------------------
def _submit(
    pool: ThreadPoolExecutor,
    label: str,
    func: Callable,
    *args,
) -> tuple[str, Future]:
    return label, pool.submit(func, *args)


def _extract_all(cfg: EtlConfig) -> dict[str, Exception]:
    """Chạy toàn bộ Extract song song. Trả về dict job_label -> exception."""
    errors: dict[str, Exception] = {}

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as pool:
        jobs: list[tuple[str, Future]] = []

        # Global jobs
        jobs.append(_submit(pool, "listing", extract_listing, cfg))
        jobs.append(_submit(pool, "macro_interbank", extract_interbank_rate, cfg))
        for idx in MACRO_SYMBOLS:
            jobs.append(_submit(pool, f"macro_index:{idx}", extract_index_prices, idx, cfg))

        # Per-symbol jobs
        for symbol in cfg.symbols:
            jobs.append(_submit(pool, f"prices:{symbol}", extract_symbol_prices, symbol, cfg))
            jobs.append(_submit(pool, f"overview:{symbol}", extract_overview, symbol, cfg))
            jobs.append(_submit(pool, f"ratio:{symbol}", extract_ratio_summary, symbol, cfg))
            jobs.append(_submit(pool, f"news:{symbol}", extract_news, symbol, cfg))
            jobs.append(_submit(pool, f"events:{symbol}", extract_events, symbol, cfg))

        label_by_future = {fut: label for label, fut in jobs}
        for fut in as_completed(label_by_future):
            label = label_by_future[fut]
            try:
                fut.result()
            except Exception as exc:  # đã retry 5 lần ở tenacity
                log.exception("Extract job failed: %s", label)
                errors[label] = exc

    return errors


def _check_failure_gate(errors: dict[str, Exception], cfg: EtlConfig) -> None:
    """Fail toàn bộ run nếu tỷ lệ mã bị lỗi PRICE > ngưỡng cho phép.

    Lỗi ở news/events/overview/ratio coi là "soft": không chặn run
    vì các cột đó có cơ chế fallback (NA hoặc NO_*_FALLBACK).
    """
    failed_symbols = {
        lbl.split(":", 1)[1]
        for lbl in errors
        if lbl.startswith("prices:")
    }
    ratio = len(failed_symbols) / max(len(cfg.symbols), 1)
    if ratio > cfg.max_fail_ratio:
        raise RuntimeError(
            f"Extract fail ratio {ratio:.1%} > {cfg.max_fail_ratio:.0%} "
            f"(failed: {sorted(failed_symbols)})"
        )
    if errors:
        log.warning("Extract finished with %d soft failures: %s", len(errors), sorted(errors.keys()))


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def run(cfg: EtlConfig) -> Path:
    setup_logging(cfg.log_dir)
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)

    log.info(
        "=== ETL RUN %s ===  symbols=%d  user_range=%s..%s  fetch_start=%s  text_mode=%s",
        cfg.run_id,
        len(cfg.symbols),
        cfg.user_start,
        cfg.user_end,
        cfg.fetch_start,
        cfg.text_mode,
    )

    # ---- EXTRACT ----------------------------------------------------------
    errors = _extract_all(cfg)
    _check_failure_gate(errors, cfg)

    # ---- TRANSFORM --------------------------------------------------------
    log.info("Transform phase starting (%d symbols)", len(cfg.symbols))
    dataset = build_full_dataset(cfg.symbols, cfg)
    if dataset.empty:
        raise RuntimeError("No rows were generated after transform. Check raw layer.")
    validate_dataset(dataset)

    # ---- LOAD -------------------------------------------------------------
    cfg.output_file.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(
        cfg.output_file,
        index=False,
        encoding="utf-8-sig",
        float_format="%.6f",
    )

    snapshot = cfg.processed_dir / f"market_data_{cfg.run_id}.csv"
    shutil.copy2(cfg.output_file, snapshot)

    log.info(
        "Done: %s rows=%d range=%s..%s symbols=%s snapshot=%s",
        cfg.output_file,
        len(dataset),
        dataset["data_date"].min(),
        dataset["data_date"].max(),
        ",".join(sorted(dataset["symbol"].unique().tolist())),
        snapshot,
    )
    return cfg.output_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_symbols(raw: str) -> list[str]:
    out: list[str] = []
    for token in raw.replace(";", ",").split(","):
        symbol = token.strip().upper()
        if symbol and symbol not in out:
            out.append(symbol)
    return out


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ETL pipeline: Extract -> Transform -> Load market_data.csv",
    )
    parser.add_argument("--start-date", default="2025-04-01")
    parser.add_argument("--end-date", default="2026-04-01")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--text-mode", default="dense", choices=["dense", "raw"])
    parser.add_argument("--output", default="market_data.csv")
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--warmup-days", type=int, default=45)
    parser.add_argument("--lake-dir", default="lake")
    parser.add_argument("--log-dir", default="logs")
    return parser


def main() -> None:
    args = _build_argparser().parse_args()
    symbols = _parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("No valid symbols. Use --symbols MBB,FPT,HPG")

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
    run(cfg)


if __name__ == "__main__":
    main()
