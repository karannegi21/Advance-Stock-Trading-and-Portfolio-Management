"""Inspect raw Kaggle NSE dataset in backend/data/"""

import glob
import os
import pandas as pd

def main():
    csv_files = [
        f for f in glob.glob("backend/data/*.csv")
        if not os.path.basename(f).startswith("stock_metadata")
    ]
    print(f"Total CSV stock files found: {len(csv_files)}")

    if not csv_files:
        print("No CSV files found in backend/data!")
        return

    sample_df = pd.read_csv(csv_files[0])
    columns = list(sample_df.columns)
    print("\n--- Dataset Columns ---")
    print(", ".join(columns))

    total_rows = 0
    min_date = None
    max_date = None
    symbols = []
    null_counts = {col: 0 for col in columns}
    symbol_stats = []

    for f in csv_files:
        sym = os.path.splitext(os.path.basename(f))[0]
        symbols.append(sym)
        df = pd.read_csv(f)
        rows = len(df)
        total_rows += rows

        for col in columns:
            if col in df.columns:
                null_counts[col] += int(df[col].isnull().sum())

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            d_min = df["Date"].min()
            d_max = df["Date"].max()
            if min_date is None or (pd.notnull(d_min) and d_min < min_date):
                min_date = d_min
            if max_date is None or (pd.notnull(d_max) and d_max > max_date):
                max_date = d_max

        turnover = 0.0
        if "Turnover" in df.columns:
            turnover = float(df["Turnover"].fillna(0).sum())
        elif "Volume" in df.columns and "Close" in df.columns:
            turnover = float((df["Volume"].fillna(0) * df["Close"].fillna(0)).sum())

        symbol_stats.append({
            "symbol": sym,
            "rows": rows,
            "start_date": str(d_min.date()) if pd.notnull(d_min) else "N/A",
            "end_date": str(d_max.date()) if pd.notnull(d_max) else "N/A",
            "turnover": turnover,
        })

    print("\n--- Dataset Summary ---")
    print(f"Total Stock Symbols: {len(symbols)}")
    print(f"Total Combined Rows: {total_rows:,}")
    print(f"Global Date Range: {min_date.date()} to {max_date.date()}")

    print("\n--- Column Null Counts ---")
    for col, count in null_counts.items():
        pct = (count / total_rows * 100) if total_rows > 0 else 0
        print(f"  {col}: {count:,} nulls ({pct:.2f}%)")

    # Check for metadata CSV if any
    meta_files = glob.glob("backend/data/*metadata*.csv")
    if meta_files:
        print(f"\nMetadata file detected: {meta_files[0]}")
        meta_df = pd.read_csv(meta_files[0])
        print("Metadata columns:", list(meta_df.columns))
        print("Metadata sample (first 3 rows):")
        print(meta_df.head(3).to_string())

    stats_df = pd.DataFrame(symbol_stats).sort_values(by="turnover", ascending=False)
    print("\n--- Top 15 Symbols by Traded Value (Turnover) ---")
    for _, row in stats_df.head(15).iterrows():
        print(f"  {row['symbol']:<15} | {row['rows']:>6} rows | {row['start_date']} to {row['end_date']} | Turnover: {row['turnover']:>18,.0f}")

    print("\n--- Bottom 5 Symbols by Rows ---")
    for _, row in stats_df.tail(5).iterrows():
        print(f"  {row['symbol']:<15} | {row['rows']:>6} rows | {row['start_date']} to {row['end_date']}")

if __name__ == "__main__":
    main()

