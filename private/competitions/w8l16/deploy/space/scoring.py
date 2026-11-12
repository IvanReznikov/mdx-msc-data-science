"""Validate and score submission CSVs against the private keys.

Deliberately stdlib-only (csv, math, random) so a submission costs ~1-2 ms of
CPU - comfortable even on the tightest free hosting tiers. Pandas is not
imported anywhere in the request path.
"""
from __future__ import annotations

import csv
import io
import math
import random
import zlib
from dataclasses import dataclass

import config


class InvalidSubmission(Exception):
    """Raised with a student-friendly message when a CSV is rejected."""


@dataclass
class Scored:
    public: float
    private: float


def load_key(comp_key: str) -> tuple[list[str], list[float], list[int]]:
    """(expected ids in order, hidden targets, public-subset indices)."""
    cfg = config.COMPETITIONS[comp_key]
    path = config.KEYS_DIR / cfg["key_file"]
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != cfg["n"]:
        raise RuntimeError(f"key file {path} has {len(rows)} rows, expected {cfg['n']}")
    ids = [normalize_id(cfg, r[cfg["id_col"]]) for r in rows]
    targets = [float(r[cfg["target_col"]]) for r in rows]
    if config.SPLIT_SEED is None:
        raise RuntimeError("SPLIT_SEED not set - export it for local runs; on the Space it is a secret (see deploy_l16_hf.py)")
    rng = random.Random(int(config.SPLIT_SEED) + zlib.crc32(comp_key.encode()))
    k = round(cfg["n"] * cfg["public_fraction"])
    public_idx = sorted(rng.sample(range(cfg["n"]), k))
    return ids, targets, public_idx


def normalize_id(cfg: dict, raw: str) -> str:
    raw = (raw or "").strip()
    if cfg["id_col"] == "row_id":          # tolerate "0", "0.0", " 0 "
        return str(int(float(raw)))
    return raw                              # dates compared verbatim (YYYY-MM-DD)


def _metric(cfg: dict, y_true: list[float], y_pred: list[float]) -> float:
    if cfg["metric"] == "rmse":
        return math.sqrt(sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true))
    return math.sqrt(sum((math.log1p(t) - math.log1p(p)) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true))


def score_submission(comp_key: str, cfg: dict, expected_ids: list[str],
                     targets: list[float], public_idx: list[int], raw: bytes) -> Scored:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InvalidSubmission("File is not valid UTF-8 text - save the CSV without special encodings.")
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(cell.strip() for cell in r)]
    if not rows:
        raise InvalidSubmission("The file is empty.")

    header = [h.strip().lstrip("\ufeff").lower() for h in rows[0]]
    want = [cfg["id_col"].lower(), cfg["target_col"].lower()]
    if header[:2] != want or len(header) != 2:
        raise InvalidSubmission(f"Header must be exactly `{cfg['id_col']},{cfg['target_col']}` "
                                f"(got {','.join(rows[0][:3])}{'...' if len(rows[0]) > 3 else ''}).")

    body = rows[1:]
    if len(body) != cfg["n"]:
        raise InvalidSubmission(f"Expected exactly {cfg['n']} data rows, got {len(body)}. "
                                f"Use sample_submission.csv as the template and fill in the target column only.")
    for i, (row, exp_id) in enumerate(zip(body, expected_ids)):
        if len(row) != 2:
            raise InvalidSubmission(f"Row {i} has {len(row)} columns - expected 2.")
        got = normalize_id(cfg, row[0])
        if got != exp_id:
            raise InvalidSubmission(f"Row {i}: {cfg['id_col']} must be `{exp_id}` (got `{got}`). "
                                    f"Keep the sample_submission order exactly as provided.")
        cell = row[1].strip()
        if not cell or cell.lower() in {"nan", "na", "null", "none"}:
            raise InvalidSubmission(f"Row {i}: missing or NaN value for `{cfg['target_col']}`.")
        try:
            val = float(cell)
        except ValueError:
            raise InvalidSubmission(f"Row {i}: `{cell}` is not a number.")
        if not math.isfinite(val):
            raise InvalidSubmission(f"Row {i}: value is not finite.")
        if val < cfg["min_value"]:
            raise InvalidSubmission(f"Row {i}: {val:g} is below {cfg['min_value']:g} - clip predictions "
                                    f"({cfg['target_col']} cannot be negative).")

    preds = [float(r[1]) for r in body]
    pub_t = [targets[i] for i in public_idx]
    pub_p = [preds[i] for i in public_idx]
    return Scored(public=_metric(cfg, pub_t, pub_p), private=_metric(cfg, targets, preds))
