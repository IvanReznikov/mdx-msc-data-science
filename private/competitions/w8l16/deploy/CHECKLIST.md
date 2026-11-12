# Deploy checklist — W8L16 leaderboard site on Hugging Face

`deploy_l16_hf.py` does every step below in one command. The manual path is
here as a fallback (and to know what the script does). Total time: ~15 min.

## Fast path (script)

```bash
cd private/competitions/w8l16/deploy

python deploy_l16_hf.py --sync --dry-run          # local sanity checks
python deploy_l16_hf.py --sync --username <you> --token hf_...   # deploy
```

Then verify (see "Verify" below). Use a **write** token for the deploy itself
(it creates repos). After deploy, swap the Space's `HF_TOKEN` secret for a
**fine-grained** token that can only *read* the keys repo and *write* the
state repo — the app never needs write access to itself.

## Manual path

1. **Keys dataset repo** (private): create `<you>/bazario-l16-keys` → upload
   `keys-repo/*` (two truth CSVs). Add `roster.csv` later (rename
   `keys-repo/roster.template.csv` after filling it) — without a roster the
   site accepts any well-formed student ID.
2. **State dataset repo** (private): create `<you>/bazario-l16-state` → upload
   `state-repo/README.txt` (any file, so the repo exists; `state.json` is
   created by the app on first submission).
3. **Fine-grained token**: read `bazario-l16-keys`, write `bazario-l16-state`.
4. **Space** (private, SDK **Docker**): create `<you>/bazario-l16-leaderboard`
   → upload everything from `space/` (including `README.md` — it carries the
   front matter). Add secrets BEFORE pushing `space/*` if doing it by hand:
   `HF_TOKEN`, `KEYS_REPO`, `STATE_REPO`, `WINDOW_CAP=5`, `WINDOW_MINUTES=15`.
5. Wait for the build (~2-3 min), open the Space.

## Verify before announcing to the class

- [ ] `https://huggingface.co/spaces/<you>/bazario-l16-leaderboard` opens, both tabs render
- [ ] Submit `keys-repo/daily_orders_hidden90.csv` as a test student → accepted, public score **0.0**
- [ ] Submit a broken CSV (wrong row count) → rejected with a clear message
- [ ] 6th submission within 15 minutes → capped with a friendly message (window resets on its own)
- [ ] Leaderboard shows the test student; `bazario-l16-state` now contains `state.json` + the audit CSV
- [ ] Delete the test student's records? Not needed — clear `state.json` in the state repo before the competition opens (or leave it, your call)

## During the competition

- The Space sleeps after **48 h idle** and wakes on the next visit (~1 min).
  Submit something yourself once a day to keep it warm during the active week.
- Submission audit trail: `bazario-l16-state` → `submissions/<comp>/<student>/`.
- Top-3 review: pull the fork notebooks, reproduce, cross-check the audit files.

## Deadline

1. Space Settings → Variables and secrets → set `REVEAL_PRIVATE` = `1` → restart Space.
2. Leaderboard now shows **final standings** (the other half of the holdout).
3. Debrief: `python private/tools/score_l16.py --scan <state-repo-clone>/submissions`
   for race-day/reseller breakdowns per student.

## After the term (rotate for the next cohort)

```bash
python private/generators/generate_l16_competitions.py --seed <new>
python deploy_l16_hf.py --sync --username <you> --token hf_...   # re-uploads keys
```
Warning students in the old fork's submissions silently stop scoring — same
policy as the warehouse generator (`--seed` rotation).

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Build fails immediately | secrets missing or `README.md` front matter not uploaded — check Space logs |
| App starts, then 500 on submit | `HF_TOKEN` secret lacks state-repo write scope |
| "This student ID is not on the roster" | `roster.csv` exists but the ID is missing — fix the roster in the keys repo |
| State write fails at submission time | the app refuses to score rather than desync — check the token and `STATE_REPO` value |
