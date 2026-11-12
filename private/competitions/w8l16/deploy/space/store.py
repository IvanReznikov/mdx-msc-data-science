"""Leaderboard state storage.

Both stores keep the same shape: a state JSON document (list of submission
records) plus an audit copy of every scored submission CSV.

- LocalStore: JSON file + submissions/ dir on disk (local runs, any host with
  a persistent disk).
- HFDatasetStore: mirrors the same state to a private Hugging Face dataset
  repo on every write, so a Space restart / 48h-idle sleep loses nothing.
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

import config


def safe_dirname(student_id: str) -> str:
    """Filesystem-safe folder name for the audit trail (names may contain spaces)."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", student_id)[:48] or "anon"


class BaseStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.records: list[dict] = []

    def load(self) -> None: ...
    def _save(self, record: dict, csv_bytes: bytes, comp: str, student_id: str, ts: str) -> None: ...

    def record(self, record: dict) -> None:
        """In-memory append only - instant, no I/O. Call persist() separately."""
        with self._lock:
            self.records.append(record)

    def add(self, record: dict, csv_bytes: bytes, comp: str, student_id: str) -> None:
        """Record the submission in memory immediately (scores/rank respond at
        once), then persist. Callers run persist in a worker thread so a slow
        HF write never blocks the event loop - a blocked loop fails health
        checks, Render replaces the instance, and everyone sees 502s."""
        self.record(record)
        self.persist(record, csv_bytes, comp, student_id)

    def persist(self, record: dict, csv_bytes: bytes, comp: str, student_id: str) -> None:
        self._save(record, csv_bytes, comp, student_id, record["ts"])

    def count_today(self, student_id: str, comp: str) -> int:
        """Scored submissions by this student for this comp inside the rolling window."""
        import datetime as _dt
        cutoff = (_dt.datetime.now(_dt.timezone.utc)
                  - _dt.timedelta(minutes=config.WINDOW_MINUTES)
                  ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return sum(1 for r in self.records
                   if r["student_id"] == student_id and r["comp"] == comp
                   and r["ts"] >= cutoff)

    def leaderboard(self, comp: str, reveal_private: bool = False) -> list[dict]:
        field = "private" if reveal_private else "public"
        best: dict[str, dict] = {}
        for r in self.records:
            if r["comp"] != comp:
                continue
            score = r[field]
            cur = best.get(r["student_id"])
            if cur is None:
                best[r["student_id"]] = {"student_id": r["student_id"], "best": score,
                                         "latest": score, "latest_ts": r["ts"], "submissions": 0}
            else:
                if score < cur["best"]:
                    cur["best"] = score
                if r["ts"] >= cur["latest_ts"]:      # latest = most recent submission's score
                    cur["latest"], cur["latest_ts"] = score, r["ts"]
            best[r["student_id"]]["submissions"] += 1
        rows = sorted(best.values(), key=lambda x: x["best"])
        for i, row in enumerate(rows, 1):
            row["rank"] = i
        return rows


class LocalStore(BaseStore):
    def __init__(self) -> None:
        super().__init__()
        self.state_path = config.DATA_DIR / "state.json"
        self.audit_dir = config.DATA_DIR / "submissions"

    def load(self) -> None:
        if self.state_path.exists():
            self.records = json.loads(self.state_path.read_text(encoding="utf-8"))

    def _save(self, record, csv_bytes, comp, student_id, ts) -> None:
        target = self.audit_dir / comp / safe_dirname(student_id)
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{ts.replace(':', '').replace('-', '')}.csv").write_bytes(csv_bytes)
        self.state_path.write_text(json.dumps(self.records, indent=1), encoding="utf-8")


class HFDatasetStore(BaseStore):
    """State lives in a private HF dataset repo; audit CSVs are uploaded too."""

    def __init__(self, repo_id: str) -> None:
        super().__init__()
        from huggingface_hub import HfApi
        self.api = HfApi(token=config.HF_TOKEN)
        self.repo_id = repo_id
        self.repo_type = "dataset"
        self._repo_ready = False      # skip the per-write create_repo roundtrip

    def load(self) -> None:
        from huggingface_hub import hf_hub_download
        try:
            path = hf_hub_download(repo_id=self.repo_id, repo_type=self.repo_type,
                                   filename="state.json", token=config.HF_TOKEN)
            self.records = json.loads(Path(path).read_text(encoding="utf-8"))
            self._repo_ready = True   # repo exists and is readable
        except Exception:
            self.records = []          # first run: repo exists but no state yet
            self._repo_ready = True    # readable repo (404 on the file only)

    def _save(self, record, csv_bytes, comp, student_id, ts) -> None:
        import io as _io
        from huggingface_hub import CommitOperationAdd, create_repo
        try:
            if not self._repo_ready:   # one-time; never per submission
                self.api.create_repo(repo_id=self.repo_id, repo_type=self.repo_type,
                                     private=True, exist_ok=True)
                self._repo_ready = True
            ops = [CommitOperationAdd(path_in_repo="state.json",
                                      path_or_fileobj=_io.BytesIO(
                                          json.dumps(self.records, indent=1).encode()))]
            audit_name = f"submissions/{comp}/{safe_dirname(student_id)}/{ts.replace(':', '').replace('-', '')}.csv"
            ops.append(CommitOperationAdd(path_in_repo=audit_name,
                                          path_or_fileobj=_io.BytesIO(csv_bytes)))
            self.api.create_commit(repo_id=self.repo_id, repo_type=self.repo_type,
                                   operations=ops, commit_message=f"submit {comp} {student_id}",
                                   token=config.HF_TOKEN)
        except Exception as exc:
            self._repo_ready = False   # re-check repo on next attempt
            raise RuntimeError(f"state backend write failed: {exc}") from exc


def get_store() -> BaseStore:
    if config.STATE_REPO and config.HF_TOKEN:
        return HFDatasetStore(config.STATE_REPO)
    return LocalStore()
