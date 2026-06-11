import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

OHLCV_DIR = Path("E:/Quarks&Quants/Non Fundamental/Hypothesis V1/Database/OHLCV")
CONSTITUENTS = Path("E:/Quarks&Quants/Non Fundamental/Hypothesis V1/Ingest/nse500_constituents.csv")
OUTPUT_DIR = Path(__file__).parent.parent / "Database"
OUTPUT_DIR.mkdir(exist_ok=True)

START_DATE = "2015-01-01"

TIMEFRAMES = {
    "daily":       "D",
    "weekly":      "W",
    "monthly":     "ME",
    "quarterly":   "QE",
    "halfyearly":  "6ME",
    "yearly":      "YE",
    "fiveyearly":  "5YE",
}


def resample_ohlcv(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    return (
        df.resample(freq)
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna(subset=["Open", "Close"])
    )


def compute_avg_range(df: pd.DataFrame, freq: str):
    resampled = df if freq == "D" else resample_ohlcv(df, freq)
    if len(resampled) < 2:
        return np.nan, np.nan
    range_abs = resampled["High"] - resampled["Low"]
    range_pct = range_abs / resampled["Close"] * 100
    return float(range_pct.mean()), float(range_abs.mean())


def main():
    constituents = pd.read_csv(CONSTITUENTS)
    meta_map = {r["Symbol"]: r.to_dict() for _, r in constituents.iterrows()}

    symbols = sorted(f.stem for f in OHLCV_DIR.glob("*.parquet"))
    print(f"Found {len(symbols)} parquet files.")

    summary_rows = []
    daily_parts = []

    for i, symbol in enumerate(symbols):
        try:
            df = pd.read_parquet(OHLCV_DIR / f"{symbol}.parquet")
            df = df[df.index >= START_DATE]
            if len(df) < 20:
                continue

            meta = meta_map.get(symbol, {})
            row = {
                "symbol": symbol,
                "company_name": meta.get("Company Name", symbol),
                "industry": meta.get("Industry", "Unknown"),
                "last_close": round(float(df["Close"].iloc[-1]), 2),
                "data_start": str(df.index.min().date()),
                "data_end": str(df.index.max().date()),
            }

            for name, freq in TIMEFRAMES.items():
                pct, abs_val = compute_avg_range(df, freq)
                row[f"{name}_range_pct"] = round(pct, 4) if not np.isnan(pct) else np.nan
                row[f"{name}_range_abs"] = round(abs_val, 2) if not np.isnan(abs_val) else np.nan

            summary_rows.append(row)

            # Daily range timeseries for charting
            daily_parts.append(pd.DataFrame({
                "symbol": symbol,
                "range_pct": ((df["High"] - df["Low"]) / df["Close"] * 100).round(4),
                "range_abs": (df["High"] - df["Low"]).round(2),
                "close": df["Close"].round(2),
            }))

        except Exception as e:
            print(f"  ERROR {symbol}: {e}")

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(symbols)} done...")

    summary = pd.DataFrame(summary_rows)
    summary.to_parquet(OUTPUT_DIR / "avg_range_summary.parquet", index=False)
    print(f"\nSaved summary: {len(summary)} stocks")

    daily_df = pd.concat(daily_parts)
    daily_df.index.name = "date"
    daily_df = daily_df.reset_index()
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    daily_df.to_parquet(OUTPUT_DIR / "daily_ranges.parquet", index=False)
    size_mb = (OUTPUT_DIR / "daily_ranges.parquet").stat().st_size / 1024 / 1024
    print(f"Saved daily ranges: {len(daily_df):,} rows  ({size_mb:.1f} MB)")
    print("\nDone.")


if __name__ == "__main__":
    main()
