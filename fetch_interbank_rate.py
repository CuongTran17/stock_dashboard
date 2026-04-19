"""Thin CLI wrapper — kéo lãi suất liên ngân hàng qua đêm vào lake/raw/.

Thay thế bản cũ dùng ``requests`` trần + ``print()``:
    - Retry tự động (tenacity) với backoff khi gặp 429 / timeout / 5xx.
    - Ghi log vào logs/etl.log thay vì print.
    - Ghi raw JSON vào lake/raw/macro_interbank/<run_id>.json để transform sau.
    - Xuất thêm CSV tiện xem tay (``lai_suat_lien_ngan_hang_qua_dem.csv``).

Ví dụ:
    python fetch_interbank_rate.py --start-date 2025-08-31 --end-date 2026-03-31

Lưu ý:
    Module ``vnstock`` >= 2.x đã gỡ bỏ data vĩ mô, không có phương án dự
    phòng chính thức -> pipeline gọi thẳng VNDirect API. Nếu API đổi schema
    thì chỉ cần sửa ``etl/extract/extract_interbank.py``.
"""
from __future__ import annotations

import argparse

import pandas as pd

from etl.config import EtlConfig
from etl.extract.extract_interbank import extract_interbank_rate, load_interbank_rate
from etl.logging_setup import get_logger, setup_logging

log = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Vietnam interbank overnight rate (raw -> lake, clean -> CSV)",
    )
    parser.add_argument("--start-date", default="2025-08-31", help="YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-03-31", help="YYYY-MM-DD")
    parser.add_argument("--output", default="lai_suat_lien_ngan_hang_qua_dem.csv")
    parser.add_argument("--lake-dir", default="lake")
    parser.add_argument("--log-dir", default="logs")
    args = parser.parse_args()

    cfg = EtlConfig.from_args(
        start_date=args.start_date,
        end_date=args.end_date,
        symbols=[],           # interbank không cần danh sách mã
        output_file=args.output,
        lake_dir=args.lake_dir,
        log_dir=args.log_dir,
        warmup_days=0,        # interbank không cần warm-up
    )
    setup_logging(cfg.log_dir)

    log.info("Fetching interbank overnight rate %s -> %s", cfg.user_start, cfg.user_end)
    raw_path = extract_interbank_rate(cfg)
    if raw_path is None:
        raise RuntimeError(
            "Kéo dữ liệu thất bại sau khi đã retry. "
            "Kiểm tra logs/etl.log hoặc thử lại sau."
        )

    df = load_interbank_rate(cfg)
    if df.empty:
        raise RuntimeError("Raw ghi xong nhưng parse ra DataFrame rỗng — schema VNDirect có thể đã đổi.")

    # Chuẩn hoá tên cột hiển thị (tương thích script cũ).
    df = df.rename(
        columns={"data_date": "Ngày", "interbank_overnight": "Lãi suất (%)"}
    )
    df["Ngày"] = pd.to_datetime(df["Ngày"])
    df = df.sort_values("Ngày").reset_index(drop=True)

    df.to_csv(cfg.output_file, index=False, encoding="utf-8-sig")
    log.info("Saved interbank CSV -> %s (%d rows)", cfg.output_file, len(df))


if __name__ == "__main__":
    main()
