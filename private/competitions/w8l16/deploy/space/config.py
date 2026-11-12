"""Configuration for the MDX-Bazario leaderboard site (instructor-only).

Add a competition by adding an entry here and dropping its key file into
KEYS_DIR - no code changes needed anywhere else.
"""
from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# Locally this file sits three levels deep in the course repo; in the Docker
# image the app is copied flat to /app, which has no such ancestor - fall back
# so import never crashes (keys then come from KEYS_REPO at startup anyway).
ROOT = _HERE.parents[2] if len(_HERE.parents) > 2 else _HERE

# Local default; on a Hugging Face Space the app bootstrap downloads the keys
# dataset repo into /tmp/keys (see app.py startup).
KEYS_DIR = Path(os.environ.get("KEYS_DIR", ROOT / "private" / "homework_keys"))
DATA_DIR = Path(os.environ.get("DATA_DIR", _HERE / "data"))      # local state dir

DAILY_CAP = int(os.environ.get("WINDOW_CAP", "5"))               # scored submissions per student/comp...
WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "15"))     # ...per rolling window of this many minutes
REVEAL_PRIVATE = os.environ.get("REVEAL_PRIVATE", "0") == "1"    # flip to 1 at the deadline -> final standings
# Optional deadline, ISO datetime (UTC assumed if no timezone), e.g. "2026-11-16T09:00:00Z".
# When set: the page shows a countdown, and submissions after it are refused (403).
# Pair with REVEAL_PRIVATE=1 at the same time for the final-standings moment.
CLOSE_AT = os.environ.get("CLOSE_AT", "").strip() or None
# Which holdout rows form the public-leaderboard subset. Deliberately NOT
# defaulted here: the Space repo is public, and seed + scoring formula would
# reveal the split. Set it as a Space secret (see deploy_l16_hf.py); for a
# local run export SPLIT_SEED=2026 (the cohort seed).
SPLIT_SEED = os.environ.get("SPLIT_SEED")
HF_TOKEN = os.environ.get("HF_TOKEN")                            # only used in hosted mode
KEYS_REPO = os.environ.get("KEYS_REPO")                          # private dataset repo holding the key files
STATE_REPO = os.environ.get("STATE_REPO")                        # private dataset repo holding leaderboard state

COMPETITIONS: dict[str, dict] = {
    "daily-orders": {
        "title": "Bazario Daily Orders - 90-day forecast",
        "metric": "rmse",
        "higher_is_better": False,
        "key_file": "daily_orders_hidden90.csv",
        "id_col": "date",
        "target_col": "orders",
        "n": 90,
        "public_fraction": 0.5,
        "min_value": 0.0,
        "unit": "orders",
        "emoji": "📦",
        "data": "2026/data/competitions/w8l16/daily_orders.csv (274 public days, 2024-01-01 .. 2024-09-30)",
        "task": "Forecast daily marketplace orders for 2024-10-01 .. 2024-12-29 (90 hidden days).",
    },
    "customer-value": {
        "title": "Bazario Customer Value - first-year spend",
        "metric": "rmsle",
        "higher_is_better": False,
        "key_file": "app_cohort_test_truth.csv",
        "id_col": "row_id",
        "target_col": "spend_12m_aed",
        "n": 600,
        "public_fraction": 0.5,
        "min_value": 0.0,
        "unit": "AED",
        "emoji": "💰",
        "data": "2026/data/competitions/w8l16/app_cohort.csv (4,600 train rows with the spend target)",
        "task": "Predict first-year spend (AED) for the 600 held-out app-cohort customers (row_id 0..599).",
    },
}
