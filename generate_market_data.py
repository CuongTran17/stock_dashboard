import argparse
from pathlib import Path

import pandas as pd
from vnstock import Vnstock

DEFAULT_SYMBOLS = ["MBB", "FPT", "HPG"]
MACRO_SYMBOLS = ["VNINDEX", "VN30", "HNXINDEX", "UPCOMINDEX"]
DEFAULT_START_DATE = "2025-04-01"
DEFAULT_END_DATE = "2026-04-01"
DEFAULT_OUTPUT_FILE = "market_data.csv"
NO_NEWS_FALLBACK = "NO_NEWS_IN_RANGE_FROM_VNSTOCK"
NO_EVENT_FALLBACK = "NO_EVENT_IN_RANGE_FROM_VNSTOCK"


def parse_symbols(symbols_arg: str) -> list[str]:
    symbols: list[str] = []
    for raw in symbols_arg.replace(";", ",").split(","):
        symbol = raw.strip().upper()
        if not symbol:
            continue
        if symbol not in symbols:
            symbols.append(symbol)
    return symbols


def calculate_rsi(close_series: pd.Series, period: int = 14) -> pd.Series:
    delta = close_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def parse_public_date_to_day(date_series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(date_series, errors="coerce")
    dt = pd.to_datetime(numeric, unit="ms", errors="coerce")
    fallback_dt = pd.to_datetime(date_series, errors="coerce")
    dt = dt.fillna(fallback_dt)
    return dt.dt.strftime("%Y-%m-%d")


def safe_get_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def prepare_macro_frame(vn: Vnstock, start_date: str, end_date: str) -> pd.DataFrame:
    base = None

    for symbol in MACRO_SYMBOLS:
        history = vn.stock(symbol=symbol, source="VCI").quote.history(
            start=start_date,
            end=end_date,
            interval="1D",
        )

        history = history.copy()
        history["data_date"] = pd.to_datetime(history["time"]).dt.strftime("%Y-%m-%d")
        prefix = symbol.lower()
        history = history.rename(
            columns={
                "open": f"macro_{prefix}_open",
                "high": f"macro_{prefix}_high",
                "low": f"macro_{prefix}_low",
                "close": f"macro_{prefix}_close",
                "volume": f"macro_{prefix}_volume",
            }
        )

        keep_cols = [
            "data_date",
            f"macro_{prefix}_open",
            f"macro_{prefix}_high",
            f"macro_{prefix}_low",
            f"macro_{prefix}_close",
            f"macro_{prefix}_volume",
        ]
        history = history[keep_cols]

        if base is None:
            base = history
        else:
            base = base.merge(history, on="data_date", how="outer")

    if base is None:
        return pd.DataFrame(columns=["data_date"])

    base = base.sort_values("data_date").reset_index(drop=True)
    return base


def fetch_company_metadata(vn: Vnstock) -> pd.DataFrame:
    listing = vn.stock(symbol="FPT", source="VCI").listing.all_symbols()
    listing = listing.rename(columns={"organ_name": "company_name"})
    listing["symbol"] = listing["symbol"].astype(str).str.upper()
    return listing[["symbol", "company_name"]]


def build_symbol_frame(
    vn: Vnstock,
    symbol: str,
    start_date: str,
    end_date: str,
    company_meta: pd.DataFrame,
    macro_frame: pd.DataFrame,
    text_mode: str,
) -> pd.DataFrame:
    stock = vn.stock(symbol=symbol, source="VCI")
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)

    history = stock.quote.history(start=start_date, end=end_date, interval="1D").copy()
    if history.empty:
        return pd.DataFrame()

    history["symbol"] = symbol
    history["data_date_dt"] = pd.to_datetime(history["time"])
    history["data_date"] = history["data_date_dt"].dt.strftime("%Y-%m-%d")

    history = history.rename(
        columns={
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
            "volume": "volume",
        }
    )

    history = history.sort_values("data_date").reset_index(drop=True)

    history["sma_7"] = history["close_price"].rolling(window=7, min_periods=7).mean()
    history["ema_21"] = history["close_price"].ewm(span=21, adjust=False).mean()
    history["rsi_14"] = calculate_rsi(history["close_price"], period=14)

    ema_fast = history["close_price"].ewm(span=12, adjust=False).mean()
    ema_slow = history["close_price"].ewm(span=26, adjust=False).mean()
    history["macd"] = ema_fast - ema_slow

    overview = stock.company.overview()
    sector = ""
    industry = ""
    if isinstance(overview, pd.DataFrame) and not overview.empty:
        overview_row = overview.iloc[0]
        sector = safe_get_text(overview_row.get("icb_name2"))
        industry = safe_get_text(overview_row.get("icb_name3"))

    history["sector"] = sector
    history["industry"] = industry

    ratio_summary = stock.company.ratio_summary()
    micro_columns = [
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

    for col in micro_columns:
        history[f"micro_{col}"] = pd.NA

    if isinstance(ratio_summary, pd.DataFrame) and not ratio_summary.empty:
        ratio_row = ratio_summary.iloc[0]
        for col in micro_columns:
            history[f"micro_{col}"] = ratio_row.get(col, pd.NA)

    news = stock.company.news()
    if isinstance(news, pd.DataFrame) and not news.empty:
        news = news.copy()
        news["data_date"] = parse_public_date_to_day(news.get("public_date"))
        news["headline"] = news.get("news_title", "").map(safe_get_text)
        news = news[news["headline"] != ""]
        news_daily = (
            news.groupby("data_date", dropna=True)["headline"]
            .apply(lambda x: " | ".join(x.head(5)))
            .reset_index()
            .rename(columns={"headline": "news_headlines"})
        )
        history = history.merge(news_daily, on="data_date", how="left")
        if text_mode == "dense":
            history = history.sort_values("data_date").reset_index(drop=True)
            history["news_headlines"] = history["news_headlines"].ffill()
            history["news_headlines"] = history["news_headlines"].fillna(NO_NEWS_FALLBACK)
        else:
            history["news_headlines"] = history["news_headlines"].fillna("")
    else:
        history["news_headlines"] = NO_NEWS_FALLBACK if text_mode == "dense" else ""

    events = stock.company.events()
    if isinstance(events, pd.DataFrame) and not events.empty:
        events = events.copy()
        events["data_date"] = parse_public_date_to_day(events.get("public_date"))
        events["event_title"] = events.get("event_title", "").map(safe_get_text)
        events = events[events["event_title"] != ""]
        events_daily = (
            events.groupby("data_date", dropna=True)["event_title"]
            .apply(lambda x: " | ".join(x.head(3)))
            .reset_index()
            .rename(columns={"event_title": "event_headlines"})
        )
        history = history.merge(events_daily, on="data_date", how="left")
        if text_mode == "dense":
            history = history.sort_values("data_date").reset_index(drop=True)
            history["event_headlines"] = history["event_headlines"].ffill()
            history["event_headlines"] = history["event_headlines"].fillna(NO_EVENT_FALLBACK)
        else:
            history["event_headlines"] = history["event_headlines"].fillna("")
    else:
        history["event_headlines"] = NO_EVENT_FALLBACK if text_mode == "dense" else ""

    history = history.merge(company_meta, on="symbol", how="left")
    history = history.merge(macro_frame, on="data_date", how="left")

    macro_columns = [
        "macro_vnindex_open",
        "macro_vnindex_high",
        "macro_vnindex_low",
        "macro_vnindex_close",
        "macro_vnindex_volume",
        "macro_vn30_open",
        "macro_vn30_high",
        "macro_vn30_low",
        "macro_vn30_close",
        "macro_vn30_volume",
        "macro_hnxindex_open",
        "macro_hnxindex_high",
        "macro_hnxindex_low",
        "macro_hnxindex_close",
        "macro_hnxindex_volume",
        "macro_upcomindex_open",
        "macro_upcomindex_high",
        "macro_upcomindex_low",
        "macro_upcomindex_close",
        "macro_upcomindex_volume",
    ]

    for col in macro_columns:
        if col in history.columns:
            history[col] = pd.to_numeric(history[col], errors="coerce")

    history = history.sort_values("data_date").reset_index(drop=True)
    history[macro_columns] = history[macro_columns].ffill().bfill()

    final_cols = [
        "symbol",
        "company_name",
        "sector",
        "industry",
        "data_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "sma_7",
        "ema_21",
        "rsi_14",
        "macd",
        "micro_pe",
        "micro_pb",
        "micro_roe",
        "micro_roa",
        "micro_eps",
        "micro_eps_ttm",
        "micro_de",
        "micro_current_ratio",
        "micro_quick_ratio",
        "micro_gross_margin",
        "micro_net_profit_margin",
        "macro_vnindex_open",
        "macro_vnindex_high",
        "macro_vnindex_low",
        "macro_vnindex_close",
        "macro_vnindex_volume",
        "macro_vn30_open",
        "macro_vn30_high",
        "macro_vn30_low",
        "macro_vn30_close",
        "macro_vn30_volume",
        "macro_hnxindex_open",
        "macro_hnxindex_high",
        "macro_hnxindex_low",
        "macro_hnxindex_close",
        "macro_hnxindex_volume",
        "macro_upcomindex_open",
        "macro_upcomindex_high",
        "macro_upcomindex_low",
        "macro_upcomindex_close",
        "macro_upcomindex_volume",
        "news_headlines",
        "event_headlines",
    ]

    for col in final_cols:
        if col not in history.columns:
            history[col] = pd.NA

    history = history[final_cols]
    history = history.sort_values(["symbol", "data_date"]).reset_index(drop=True)
    if text_mode == "dense":
        history["news_headlines"] = history["news_headlines"].fillna(NO_NEWS_FALLBACK)
        history["event_headlines"] = history["event_headlines"].fillna(NO_EVENT_FALLBACK)
    else:
        history["news_headlines"] = history["news_headlines"].fillna("")
        history["event_headlines"] = history["event_headlines"].fillna("")

    history = history[
        (pd.to_datetime(history["data_date"]) >= start_ts)
        & (pd.to_datetime(history["data_date"]) <= end_ts)
    ].reset_index(drop=True)

    return history


def build_dataset(start_date: str, end_date: str, text_mode: str, symbols: list[str]) -> pd.DataFrame:
    vn = Vnstock()
    company_meta = fetch_company_metadata(vn)
    macro_frame = prepare_macro_frame(vn, start_date, end_date)

    frames = []
    for symbol in symbols:
        frame = build_symbol_frame(
            vn=vn,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            company_meta=company_meta,
            macro_frame=macro_frame,
            text_mode=text_mode,
        )
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["symbol", "data_date"]).reset_index(drop=True)
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate market_data.csv using vnstock")
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
        help="dense: fill headline gaps for every row, raw: keep only true daily news/events",
    )
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    if not symbols:
        raise ValueError("No valid symbols provided. Use --symbols, e.g. --symbols MBB,FPT,HPG")

    output_path = Path(args.output)

    dataset = build_dataset(
        start_date=args.start_date,
        end_date=args.end_date,
        text_mode=args.text_mode,
        symbols=symbols,
    )
    if dataset.empty:
        raise RuntimeError("No rows were generated. Check symbol availability and date range.")

    dataset.to_csv(output_path, index=False, encoding="utf-8-sig", float_format="%.6f")

    print(f"Generated: {output_path.resolve()}")
    print(f"Rows: {len(dataset)}")
    print(f"Date range: {dataset['data_date'].min()} -> {dataset['data_date'].max()}")
    print("Symbols:", ", ".join(sorted(dataset['symbol'].unique().tolist())))


if __name__ == "__main__":
    main()
