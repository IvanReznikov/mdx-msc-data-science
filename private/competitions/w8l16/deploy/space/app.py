"""MDX-Bazario W8L16 leaderboard site - two tabs: submit CSV, view leaderboard.

Run locally:   uvicorn app:app --reload --port 8000   (from this directory)
On HF Spaces:  private Docker Space; KEYS_REPO/STATE_REPO/HF_TOKEN secrets set.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import re
import shutil
import sys
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Container-visible logging: Render captures stdout; make every startup step,
# submission and failure show up in the Logs tab with a timestamp.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("leaderboard")
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

import config
import scoring
from store import get_store

app = FastAPI(title="MDX-Bazario Leaderboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

TEMPLATE = (Path(__file__).resolve().parent / "templates" / "index.html").read_text(encoding="utf-8")
STORE = get_store()
# A name, not an ID: letters (any script), spaces, digits, . ' - _ ; no path/control
# characters. Length 1-40, at least one letter.
STUDENT_RE = re.compile(r"^[^\f\n\r\t\v/\\:*?\"<>|]{1,40}$")
KEYS: dict[str, tuple] = {}
HEALTH = {"keys_ok": False, "state_ok": False}


@app.on_event("startup")
def startup() -> None:
    """Pull keys + state at boot. Crash-proof on purpose: a transient HF
    failure must degrade the service, never crash-loop it (that shows up as
    endless 502s). /api/health reports what actually loaded."""
    log.info("startup begin | host keys_dir=%s | KEYS_REPO=%s | STATE_REPO=%s | split_seed_set=%s",
             config.KEYS_DIR, bool(config.KEYS_REPO), bool(config.STATE_REPO),
             config.SPLIT_SEED is not None)
    if config.KEYS_REPO and config.HF_TOKEN:
        from huggingface_hub import snapshot_download
        target = Path("/tmp/keys")
        for attempt in range(1, 4):
            try:
                shutil.rmtree(target, ignore_errors=True)
                snapshot_download(repo_id=config.KEYS_REPO, repo_type="dataset",
                                  local_dir=str(target), token=config.HF_TOKEN)
                config.KEYS_DIR = target
                log.info("keys repo downloaded (attempt %d) -> %s", attempt, target)
                break
            except Exception:
                log.exception("keys download failed (attempt %d/3)", attempt)
                time.sleep(3 * attempt)
        else:
            log.error("giving up on keys repo after 3 attempts - scoring will 500 until restart")
    try:
        STORE.load()
        HEALTH["state_ok"] = True
        log.info("state loaded: %d records (%s)", len(STORE.records), type(STORE).__name__)
    except Exception:
        log.exception("state load FAILED - serving with empty in-memory state")
    for comp_key, cfg in config.COMPETITIONS.items():
        try:
            KEYS[comp_key] = scoring.load_key(comp_key)
            HEALTH["keys_ok"] = True
            log.info("key loaded: %s (%d rows)", comp_key, len(KEYS[comp_key][0]))
        except Exception:
            log.exception("key load FAILED for %s", comp_key)
    log.info("startup done | health=%s", HEALTH)


def _roster() -> set[str] | None:
    path = config.KEYS_DIR / "roster.csv"
    if not path.exists():
        return None
    import csv
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["student_id"].strip() for r in csv.DictReader(fh)}


@app.get("/", response_class=HTMLResponse)
def index():
    comps = {k: {"title": c["title"], "metric": c["metric"].upper(), "unit": c["unit"],
                 "emoji": c.get("emoji", ""), "data": c["data"], "task": c["task"], "n": c["n"],
                 "target": c["target_col"], "id": c["id_col"]}
             for k, c in config.COMPETITIONS.items()}
    return TEMPLATE.replace("__COMPS__", json.dumps(comps)) \
                   .replace("__DAILY_CAP__", str(config.DAILY_CAP)) \
                   .replace("__WINDOW_MINUTES__", str(config.WINDOW_MINUTES)) \
                   .replace("__REVEAL__", "true" if config.REVEAL_PRIVATE else "false") \
                   .replace("__CLOSE_AT__", config.CLOSE_AT or "")


@app.get("/api/health")
def health():
    return {"ok": True, "records": len(STORE.records), **HEALTH,
            "uptime_note": "degraded - see logs" if not (HEALTH["keys_ok"] and HEALTH["state_ok"]) else "all good"}


@app.get("/api/leaderboard")
def leaderboard():
    out = {}
    for comp_key, cfg in config.COMPETITIONS.items():
        rows = STORE.leaderboard(comp_key, reveal_private=config.REVEAL_PRIVATE)
        out[comp_key] = {
            "title": cfg["title"], "metric": cfg["metric"].upper(),
            "unit": cfg["unit"], "reveal_private": config.REVEAL_PRIVATE,
            "rows": rows,
        }
    return JSONResponse(out)


@app.get("/api/sample/{comp}")
def sample_csv(comp: str):
    """Stream the sample submission (ids only, never the truth) for download."""
    import csv
    import io

    from fastapi.responses import Response

    if comp not in config.COMPETITIONS:
        raise HTTPException(404, "Unknown competition.")
    cfg = config.COMPETITIONS[comp]
    ids, _targets, _public = KEYS[comp]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([cfg["id_col"], cfg["target_col"]])
    for i in ids:
        w.writerow([i, ""])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="sample_submission_{comp}.csv"'})


@app.post("/api/submit")
async def submit(student_id: str = Form(...), comp: str = Form(...), file: UploadFile = File(...)):
    student_id = " ".join((student_id or "").split())
    if not (STUDENT_RE.match(student_id) and any(ch.isalpha() for ch in student_id)):
        raise HTTPException(400, "Please enter your name (1-40 chars; letters, spaces, digits, . ' - _).")
    if comp not in config.COMPETITIONS:
        raise HTTPException(400, "Unknown competition.")
    roster = _roster()
    if roster is not None and student_id not in roster:
        raise HTTPException(400, "This name is not on the course roster - check the spelling.")
    if config.CLOSE_AT:
        close = dt.datetime.fromisoformat(config.CLOSE_AT.replace("Z", "+00:00"))
        if close.tzinfo is None:
            close = close.replace(tzinfo=dt.timezone.utc)
        if dt.datetime.now(dt.timezone.utc) >= close:
            raise HTTPException(403, "Competitions are closed - the deadline has passed. "
                                     "Final standings will be published in the debrief.")

    raw = await file.read()
    if len(raw) > 2_000_000:
        log.info("reject %s %s: file too large (%d bytes)", student_id, comp, len(raw))
        raise HTTPException(400, "File larger than 2 MB - a submission is 90 or 600 rows.")
    cfg = config.COMPETITIONS[comp]
    if comp not in KEYS:
        log.error("submit while keys unavailable for %s - startup load failed", comp)
        raise HTTPException(503, "Scoring is temporarily unavailable - the service is degraded. Try again in a minute.")
    expected_ids, targets, public_idx = KEYS[comp]
    try:
        scored = scoring.score_submission(comp, cfg, expected_ids, targets, public_idx, raw)
    except scoring.InvalidSubmission as exc:
        log.info("reject %s %s: %s", student_id, comp, exc)
        raise HTTPException(400, str(exc))
    log.info("scored %s %s: public=%.4f private=%.4f", student_id, comp, scored.public, scored.private)

    if STORE.count_today(student_id, comp) >= config.DAILY_CAP:
        log.info("reject %s %s: window cap reached", student_id, comp)
        raise HTTPException(429, f"Rate limit: max {config.DAILY_CAP} scored submissions per "
                                 f"{config.WINDOW_MINUTES} minutes. Try again shortly.")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    record = {"comp": comp, "student_id": student_id, "ts": ts,
              "public": round(scored.public, 6), "private": round(scored.private, 6),
              "filename": file.filename[:120]}
    try:
        t0 = time.time()
        STORE.record(record)           # memory append: scores/rank respond instantly
        # HF persist off the event loop: a slow HF commit (tens of seconds) must
        # never freeze health checks - that is what caused the 502 + instance
        # replacement loop.
        await run_in_threadpool(STORE.persist, record, raw, comp, student_id)
        log.info("stored %s %s (state write took %.1fs)", student_id, comp, time.time() - t0)
    except RuntimeError as exc:
        log.exception("state write FAILED for %s %s", student_id, comp)
        raise HTTPException(500, str(exc))

    mine = [r for r in STORE.records if r["comp"] == comp and r["student_id"] == student_id]
    best_before = min((r["public"] for r in mine[:-1]), default=None)
    improved = best_before is None or record["public"] < best_before
    best = record["public"] if improved else best_before
    rows = STORE.leaderboard(comp, reveal_private=False)
    rank = next((r["rank"] for r in rows if r["student_id"] == student_id), None)
    remaining = max(0, config.DAILY_CAP - STORE.count_today(student_id, comp))
    verb = "New best!" if best_before is not None and improved else "Accepted."
    return {"ok": True, "comp": comp, "current": record["public"], "best": best,
            "metric": cfg["metric"].upper(), "rank": rank, "improved": improved,
            "remaining_window": remaining,
            "message": f"{verb} Current score ({cfg['metric'].upper()}): {record['public']:.4f} · "
                       f"your best: {best:.4f} · "
                       f"{remaining} submission(s) left in the next {config.WINDOW_MINUTES} min."}
