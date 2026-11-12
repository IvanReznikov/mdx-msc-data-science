# RENDER.md — host the leaderboard on Render (free), state on HF

Why the pivot: since 2025 Hugging Face **requires a PRO subscription** for
Docker/Gradio Spaces on free accounts (deploy attempt returned
`402 Payment Required`; only *Static* Spaces stay free — no Python backend).
Render's free plan runs our Docker image as-is, and the already-created
**private HF datasets** keep holding keys + state, so nothing about the
architecture changes.

| Piece | Where |
|---|---|
| App (Docker) | Render free web service ( sleeps after 15 min idle → kept warm by a GitHub Action ) |
| Keys + roster | HF private dataset `ce1ebi/bazario-l16-keys` (already uploaded) |
| State + audit trail | HF private dataset `ce1ebi/bazario-l16-state` (already created) |
| Split seed | Render secret `SPLIT_SEED` (never in the repo) |

## Deploy (one-time, ~10 min of clicks)

1. **Push this repo to GitHub** (private) — Render builds from it. Make sure
   `private/competitions/w8l16/deploy/space/` and root `render.yaml` are committed.
2. **Sign up** at render.com (Log in with GitHub — grants access to this private repo).
3. Dashboard → **New → Blueprint** → pick this repo. Render reads `render.yaml`.
4. It prompts for the two `sync: false` secrets:
   - `HF_TOKEN` — the token from `.env` (it already read/write the two datasets);
     better: make a fine-grained one (read keys repo, write state repo).
   - `SPLIT_SEED` — `2026`.
5. **Apply** → wait for the build (~3–5 min; image pull + pip install).
   Health check `/api/health` must pass → service goes Live.
6. Copy the URL (`https://bazario-l16-leaderboard.onrender.com`), then in the
   **GitHub repo**: Settings → Secrets and variables → Variables → Actions →
   New variable `L16_URL` = that URL. The keep-warm workflow (every 10 min)
   starts on the next schedule tick.

## Acceptance test (5 min, before announcing)

Run `RELEASE.md` Phase 2 step 6 against the Render URL — summary:
- `GET /api/health` → `{"ok": true, ...}`
- submit `deploy/keys-repo/daily_orders_hidden90.csv` as `testuser` → public score **0.0**, chips show current/best
- 5 more rapid submissions → 6th gets the 15-minute rate-limit message
- broken CSV (e.g. 50 rows) → friendly rejection
- leaderboard lists `testuser`; HF state repo shows `state.json` + audit CSV
- then reset: set `state.json` → `[]` in the state repo (web UI edit) and delete
  its `submissions/` folder; Render → Manual Deploy → **Restart** not needed
  (state is pulled at startup → DO restart after editing state.json).

## Ops on Render

| Task | How |
|---|---|
| Reveal final standings | service → Environment → add `REVEAL_PRIVATE=1` → Save (triggers deploy) |
| Add roster | upload `roster.csv` to the keys dataset repo → service → Manual Deploy → Restart (keys snapshot at boot) |
| New cohort | regenerate + `--sync` + push repo → Manual Deploy → Deploy latest commit; re-upload keys dataset |
| Logs / errors | service → Logs (scoring rejects, HF writes all visible) |

Free-plan limits: 512 MB RAM (plenty), sleeps after 15 min idle (keep-warm
handles it; worst case ~1 min cold start), 750 h/month (a web service is ~730 h).

## Alternatives (kept for reference)

- **HF PRO ($9/mo)**: rerun `deploy_l16_hf.py --sync` unchanged — everything else already works.
- **PythonAnywhere free**: zero sleep + persistent disk, but WSGI-only → needs a small ASGI adapter; ~100 CPU-s/day is fine for the stdlib scorer.
