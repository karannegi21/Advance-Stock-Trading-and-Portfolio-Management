"""Seed market data script for Kaggle NSE dataset (2015-01-01 to 2021-04-30).

Features:
- Metadata mapping from stock_metadata.csv
- Sanitization: high >= max(open, close), low <= min(open, close)
- Logs per-symbol sanitization changes
- Skips symbols with < 500 bars in window
- 100% Idempotent insertion
- Initializes simulator state
"""

import glob
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.config import settings
from app.models.stock import PriceBar, Stock
from app.models.simulator import SimState


START_DATE = "2015-01-01"
END_DATE = "2021-04-30"
MIN_BARS_THRESHOLD = 500
BATCH_SIZE = 5000


def load_metadata(data_dir: str) -> Dict[str, Tuple[str, str]]:
    """Load metadata mapping: symbol -> (company_name, sector)."""
    meta_path = os.path.join(data_dir, "stock_metadata.csv")
    mapping = {}
    if os.path.exists(meta_path):
        try:
            df = pd.read_csv(meta_path)
            for _, row in df.iterrows():
                sym = str(row.get("Symbol", "")).strip().upper()
                name = str(row.get("Company Name", sym)).strip()
                sector = str(row.get("Industry", "Unknown")).strip()
                if sym:
                    mapping[sym] = (name, sector)
        except Exception as e:
            print(f"Warning: Failed to parse stock_metadata.csv: {e}")
    return mapping


def seed_data():
    print("=" * 60)
    print(f"Starting Market Data Seeding [{START_DATE} to {END_DATE}]")
    print("=" * 60)

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    csv_files = [
        f for f in glob.glob(os.path.join(data_dir, "*.csv"))
        if not os.path.basename(f).startswith("stock_metadata")
        and not os.path.basename(f).startswith("NIFTY50_all")
    ]

    print(f"Discovered {len(csv_files)} candidate stock CSV files in {data_dir}")
    metadata = load_metadata(data_dir)

    engine = create_engine(settings.sync_database_url)

    skipped_symbols: List[Tuple[str, int, str]] = []
    sanitization_logs: List[Tuple[str, int]] = []
    processed_symbols = 0
    total_bars_inserted = 0

    overall_min_date = None
    overall_max_date = None

    with engine.connect() as conn:
        for filepath in sorted(csv_files):
            symbol = os.path.splitext(os.path.basename(filepath))[0].strip().upper()
            
            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                skipped_symbols.append((symbol, 0, f"Read error: {e}"))
                continue

            if df.empty or "Date" not in df.columns:
                skipped_symbols.append((symbol, 0, "Empty or missing Date column"))
                continue

            # Parse and filter date window
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])
            mask = (df["Date"] >= pd.to_datetime(START_DATE)) & (df["Date"] <= pd.to_datetime(END_DATE))
            window_df = df.loc[mask].copy()

            count = len(window_df)
            if count < MIN_BARS_THRESHOLD:
                skipped_symbols.append((symbol, count, f"Fewer than {MIN_BARS_THRESHOLD} bars ({count})"))
                continue

            # Drop duplicate dates if any, keeping latest
            window_df = window_df.sort_values(by="Date").drop_duplicates(subset=["Date"], keep="last")

            # Sanitization logic: high >= max(open, close), low <= min(open, close)
            sanitized_count = 0
            bars_to_insert = []

            for _, row in window_df.iterrows():
                trade_date = row["Date"].date()
                open_val = float(row["Open"]) if pd.notnull(row["Open"]) else float(row["Close"])
                high_val = float(row["High"]) if pd.notnull(row["High"]) else max(open_val, float(row["Close"]))
                low_val = float(row["Low"]) if pd.notnull(row["Low"]) else min(open_val, float(row["Close"]))
                close_val = float(row["Close"]) if pd.notnull(row["Close"]) else open_val
                volume_val = int(row["Volume"]) if pd.notnull(row["Volume"]) else 0

                adj_high = max(high_val, open_val, close_val)
                adj_low = min(low_val, open_val, close_val)

                if adj_high != high_val or adj_low != low_val:
                    sanitized_count += 1

                bars_to_insert.append({
                    "trade_date": trade_date,
                    "open": round(Decimal(str(open_val)), 4),
                    "high": round(Decimal(str(adj_high)), 4),
                    "low": round(Decimal(str(adj_low)), 4),
                    "close": round(Decimal(str(close_val)), 4),
                    "volume": volume_val,
                })

                if overall_min_date is None or trade_date < overall_min_date:
                    overall_min_date = trade_date
                if overall_max_date is None or trade_date > overall_max_date:
                    overall_max_date = trade_date

            sanitization_logs.append((symbol, sanitized_count))

            # Upsert Stock row
            company_name, sector = metadata.get(symbol, (symbol, "Unknown"))
            stock_stmt = (
                pg_insert(Stock)
                .values(
                    symbol=symbol,
                    name=company_name,
                    sector=sector,
                    is_active=True,
                )
                .on_conflict_do_update(
                    index_elements=["symbol"],
                    set_={"name": company_name, "sector": sector, "is_active": True},
                )
                .returning(Stock.id)
            )
            stock_id = conn.execute(stock_stmt).scalar_one()

            # Batch upsert PriceBars
            for i in range(0, len(bars_to_insert), BATCH_SIZE):
                chunk = bars_to_insert[i : i + BATCH_SIZE]
                chunk_values = [
                    {
                        "stock_id": stock_id,
                        "trade_date": bar["trade_date"],
                        "open": bar["open"],
                        "high": bar["high"],
                        "low": bar["low"],
                        "close": bar["close"],
                        "volume": bar["volume"],
                    }
                    for bar in chunk
                ]

                bar_stmt = (
                    pg_insert(PriceBar)
                    .values(chunk_values)
                    .on_conflict_do_update(
                        constraint="uq_stock_trade_date",
                        set_={
                            "open": pg_insert(PriceBar).excluded.open,
                            "high": pg_insert(PriceBar).excluded.high,
                            "low": pg_insert(PriceBar).excluded.low,
                            "close": pg_insert(PriceBar).excluded.close,
                            "volume": pg_insert(PriceBar).excluded.volume,
                        },
                    )
                )
                conn.execute(bar_stmt)

            conn.commit()
            processed_symbols += 1
            total_bars_inserted += len(bars_to_insert)
            print(f"[{processed_symbols:>2}] Seeded {symbol:<12}: {len(bars_to_insert):>5} bars (sanitized rows: {sanitized_count})")

        # Initialize or update SimState
        if overall_min_date:
            sim_stmt = (
                pg_insert(SimState)
                .values(
                    id=1,
                    current_sim_date=overall_min_date,
                    speed_seconds_per_day=settings.SIMULATOR_SPEED_SECONDS,
                    is_running=False,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"current_sim_date": overall_min_date},
                )
            )
            conn.execute(sim_stmt)
            conn.commit()

        # Final Verification Queries
        total_stocks = conn.execute(select(func.count(Stock.id))).scalar_one()
        total_bars = conn.execute(select(func.count(PriceBar.id))).scalar_one()
        min_date_res = conn.execute(select(func.min(PriceBar.trade_date))).scalar_one()
        max_date_res = conn.execute(select(func.max(PriceBar.trade_date))).scalar_one()

    print("\n" + "=" * 60)
    print("SANITIZATION SUMMARY (Rows changed per symbol)")
    print("=" * 60)
    for sym, count in sanitization_logs:
        print(f"  {sym:<15} : {count:>4} rows sanitized")

    print("\n" + "=" * 60)
    print("SKIPPED SYMBOLS (< 500 bars in window or invalid)")
    print("=" * 60)
    if skipped_symbols:
        for sym, bars, reason in skipped_symbols:
            print(f"  {sym:<15} (bars: {bars:>4}) -> {reason}")
    else:
        print("  None! All symbols had >= 500 bars.")

    print("\n" + "=" * 60)
    print("DATABASE SEEDING FINAL AUDIT")
    print("=" * 60)
    print(f"  Total Stocks in DB       : {total_stocks}")
    print(f"  Total Price Bars in DB   : {total_bars:,}")
    print(f"  Minimum Trade Date       : {min_date_res}")
    print(f"  Maximum Trade Date       : {max_date_res}")
    print("=" * 60)


if __name__ == "__main__":
    seed_data()

