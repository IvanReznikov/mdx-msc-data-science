# HF deployment folder — W8L16 leaderboard (self-contained)

Everything needed to put the leaderboard site on Hugging Face, in one folder:

| Item | What |
|---|---|
| `deploy_l16_hf.py` | one-command deployer — creates the private keys/state dataset repos + private Docker Space, uploads everything, sets secrets. `--dry-run` verifies locally; `--sync` refreshes the snapshots from the live sources first |
| `space/` | the complete Space payload (FastAPI app, Dockerfile, HF front-matter README) |
| `keys-repo/` | the only key files the site needs (`daily_orders_hidden90.csv`, `app_cohort_test_truth.csv`) + `roster.template.csv` |
| `state-repo/` | stub for the state/audit dataset repo (state.json auto-created) |
| `CHECKLIST.md` | deploy + verify + deadline + rotation procedures |

Start here: **`python deploy_l16_hf.py --sync --dry-run`**, then follow
`CHECKLIST.md`. Never commit real student IDs except in the keys repo
(private dataset).

Note: `space/` and the key files are refreshed from the live sources
(`private/tools/leaderboard_site/`, `private/homework_keys/`) on every
`--sync`, so the snapshots can't drift.
