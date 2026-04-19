"""Cấu hình tập trung cho ETL pipeline.

Tất cả hằng số (symbols mặc định, cột, đường dẫn lake, tham số warm-up,
concurrency, fail ratio) đều đặt ở đây để các module khác chỉ cần import.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Danh mục mã & tập cột cố định
# ---------------------------------------------------------------------------
DEFAULT_SYMBOLS: list[str] = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
]
MACRO_SYMBOLS: list[str] = ["VNINDEX", "VN30", "HNXINDEX", "UPCOMINDEX"]

NO_NEWS_FALLBACK = "NO_NEWS_IN_RANGE_FROM_VNSTOCK"
NO_EVENT_FALLBACK = "NO_EVENT_IN_RANGE_FROM_VNSTOCK"

MICRO_COLUMNS: list[str] = [
    "pe",
    "pb",
    "roe",
    "roa",
    "eps",
    "eps_ttm",
    "de",
    "current_ratio",
    "quick_ratio",
    "gross_margin",
    "net_profit_margin",
]

# Danh sách macro numeric columns sẽ được ffill (KHÔNG bfill) ở bước transform.
MACRO_NUMERIC_COLUMNS: list[str] = [
    f"macro_{prefix}_{suffix}"
    for prefix in ("vnindex", "vn30", "hnxindex", "upcomindex")
    for suffix in ("open", "high", "low", "close", "volume")
]


# ---------------------------------------------------------------------------
# Cấu hình run-time
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EtlConfig:
    """Cấu hình cho một lần chạy ETL.

    Lưu ý về warm-up:
        ``fetch_start`` luôn lùi trước ``user_start`` một khoảng đủ để các chỉ
        báo kỹ thuật (EMA21, MACD 12/26/9, RSI14) hội tụ. Sau khi tính xong,
        bước transform sẽ cắt lại đúng ``[user_start, user_end]``.
    """

    user_start: date
    user_end: date
    symbols: list[str] = field(default_factory=lambda: list(DEFAULT_SYMBOLS))
    text_mode: str = "dense"  # "dense" | "raw"

    # Warm-up: 45 phiên * 2 ≈ 90 ngày lịch → phủ đủ EMA/MACD/RSI, kể cả nghỉ lễ.
    warmup_days: int = 45

    # Concurrency / fault tolerance.
    max_workers: int = 6
    max_fail_ratio: float = 0.05

    # Đường dẫn lake / logs / output.
    lake_dir: Path = Path("lake")
    log_dir: Path = Path("logs")
    output_file: Path = Path("market_data.csv")

    # Identifier đóng băng cho mỗi lần chạy.
    run_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%dT%H%M%S"))

    # --- Derived paths -----------------------------------------------------
    @property
    def fetch_start(self) -> date:
        """Ngày bắt đầu fetch (lùi trước để warm-up indicator)."""
        return self.user_start - timedelta(days=self.warmup_days * 2)

    @property
    def raw_dir(self) -> Path:
        return self.lake_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.lake_dir / "processed"

    # --- Helpers -----------------------------------------------------------
    def raw_path(self, category: str, symbol: str | None = None, suffix: str = "csv") -> Path:
        """Trả về path chuẩn hoá để ghi raw.

        Ví dụ:
            raw_path("prices", "FPT", "csv")
            -> lake/raw/prices/FPT/<run_id>.csv
            raw_path("macro_interbank", suffix="json")
            -> lake/raw/macro_interbank/<run_id>.json
        """
        base = self.raw_dir / category
        if symbol:
            base = base / symbol.upper()
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{self.run_id}.{suffix}"

    @staticmethod
    def parse_date(value: str | date) -> date:
        if isinstance(value, date):
            return value
        return datetime.strptime(value, "%Y-%m-%d").date()

    @classmethod
    def from_args(
        cls,
        start_date: str | date,
        end_date: str | date,
        symbols: list[str],
        text_mode: str = "dense",
        output_file: str | Path = "market_data.csv",
        max_workers: int = 6,
        warmup_days: int = 45,
        lake_dir: str | Path = "lake",
        log_dir: str | Path = "logs",
    ) -> "EtlConfig":
        return cls(
            user_start=cls.parse_date(start_date),
            user_end=cls.parse_date(end_date),
            symbols=list(symbols),
            text_mode=text_mode,
            output_file=Path(output_file),
            max_workers=max_workers,
            warmup_days=warmup_days,
            lake_dir=Path(lake_dir),
            log_dir=Path(log_dir),
        )
