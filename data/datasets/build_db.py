"""Build a single SQLite database from the repo's tabular datasets.

Usage (repo venv):  python data/datasets/build_db.py [--db data/datasets/datasets.db] [--include-big]

Design decisions
- SQLite (stdlib, zero-install, DB Browser opens it) is the *derived, convenience* copy;
  the CSVs stay canonical - pandas-first teaching is unaffected.
- Every CSV becomes a table named after its file (normalised: lower-case, non-alnum -> _).
- Big text tables (OnlineRetail variants) are opt-in via --include-big.
- The .db is gitignored (regenerable). Rebuild after adding datasets.
- For analytical SQL teaching prefer duckdb over this file (see alternatives/04); SQLite
  exists here because every laptop can open it with zero installs.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BIG = {"OnlineRetail.csv", "OnlineRetail_utf8.csv", "retail_large_noisy.csv",
       "bank-additional-full.csv", "hotel_bookings.csv", "cardio_train.csv",
       "prices-split-adjusted.csv"}

SKIP_SUFFIXES = (".zip", ".npz", ".data")
SKIP_DIRS = True  # subdirectories (glass/, brain_tumor_dataset/...) hold non-tabular assets


def table_name(stem: str) -> str:
    keep = "".join(c if c.isalnum() else "_" for c in stem.lower())
    while "__" in keep:
        keep = keep.replace("__", "_")
    return keep.strip("_")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=HERE / "datasets.db")
    ap.add_argument("--include-big", action="store_true",
                    help="also load the multi-100k-row tables (db grows to ~100 MB)")
    args = ap.parse_args()

    if args.db.exists():
        args.db.unlink()

    loaded = []
    with sqlite3.connect(args.db) as con:
        for csv in sorted(HERE.glob("*.csv")):
            if not args.include_big and csv.name in BIG:
                continue
            try:
                with open(csv, "r", encoding="utf-8", errors="replace") as fh:
                    first = fh.readline()
                sep = ";" if first.count(";") > first.count(",") else ","
                df = pd.read_csv(csv, sep=sep, low_memory=False)
            except Exception as e:  # unreadable/odd encodings -> skip loudly
                print(f"skip {csv.name}: {e}")
                continue
            df.columns = [table_name(str(c)) for c in df.columns]
            df.to_sql(table_name(csv.stem), con, index=False)
            loaded.append((table_name(csv.stem), len(df), len(df.columns)))

    w = max(len(t) for t, _, _ in loaded)
    for t, r, c in loaded:
        print(f"{t:<{w}}  {r:>9,} rows x {c:>3} cols")
    print(f"\n{len(loaded)} tables -> {args.db} ({args.db.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
