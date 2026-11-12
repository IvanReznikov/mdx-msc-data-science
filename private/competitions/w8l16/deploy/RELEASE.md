# RELEASE.md — W8L16 leaderboard challenge, step-by-step

From "everything built" to "debrief done". Times assume a class of ~45.
Work from the repo root unless a step says otherwise. `PY` = `.venv/Scripts/python.exe`.

## Phase 0 — prerequisites (one-time, ~10 min)

- [ ] **Hugging Face account** you'll host under (free). Phone-verify it if not already.
- [ ] **Deploy token**: hf.co/settings/tokens → *New token* → **Write** access (creates repos).
  Fine-grained read-keys/write-state token comes later (step 13).
- [ ] **Roster** (optional but recommended): fill `keys-repo/roster.template.csv`
  (one `student_id` per line) and rename to `roster.csv`. Without it the site
  accepts any well-formed student ID.

## Phase 1 — pre-flight in the repo (~10 min, do the week before)

1. **Regenerate with the cohort seed** (default 2026; rotate per cohort):
   ```bash
   $PY private/generators/generate_l16_competitions.py --seed 2026
   ```
   Expect: public 274 rows / hidden 90; hidden race days list; reseller median ≈ 88k vs standard ≈ 4.6k.
2. **Re-verify the difficulty ladders** (~4 min):
   ```bash
   $PY private/tools/verify_l16_puzzle.py --plot
   ```
   Expect roughly: comp1 naive ~703 → blind MLP ~722 → discovered ~243; comp2 median ~0.87 → blind MLP ~0.41 → HGB ~0.31.
   Plots land in `private/homework_keys/l16_*.png` (races orange/grey, sale days green dashed).
3. **Smoke-test the student templates** (copy both templates to a scratch dir, Run All in
   Jupyter, confirm two `submission_*.csv` appear and score at the entry-ticket values):
   ```bash
   $PY private/tools/score_l16.py --comp daily-orders   --submission <scratch>/submission_daily-orders.csv
   $PY private/tools/score_l16.py --comp customer-value --submission <scratch>/submission_customer-value.csv
   ```
   Expect: RMSE ~703 / RMSLE ~0.87 (the baselines). Delete the scratch dir.
4. **Dry-run the deploy bundle** (checks snapshots, key row counts, front matter):
   ```bash
   $PY private/competitions/w8l16/deploy/deploy_l16_hf.py --sync --dry-run
   ```
   Expect: no MISSING lines, exit 0.

## Phase 2 — deploy the site (~15 min, do ≥3 days before release)

> **2026 platform note:** HF free accounts can no longer host Docker Spaces (402 — PRO only).
> The default host is now **Render free** — follow `RENDER.md`. The HF datasets (keys/state)
> are already created and uploaded; `deploy_l16_hf.py` still works verbatim if you have HF PRO.

5. **Deploy everything** (creates 2 private datasets + 1 private Docker Space, uploads,
   sets secrets):
   ```bash
   $PY private/competitions/w8l16/deploy/deploy_l16_hf.py --sync \
        --username <your-hf-name> --token hf_xxx
   ```
   Save the three URLs it prints. Build takes ~2–3 min.
6. **Acceptance test** on `https://huggingface.co/spaces/<you>/bazario-l16-leaderboard`:
   - [ ] both tabs render;
   - [ ] submit `deploy/keys-repo/daily_orders_hidden90.csv` as `testuser` → accepted, **public score 0.0**;
   - [ ] submit it 5× fast → 6th rejected: *rate limit … per 15 minutes*;
   - [ ] wrong-row-count CSV → friendly rejection;
   - [ ] leaderboard shows `testuser`; state repo now has `state.json` + audit CSV;
   - [ ] score chips show *This submission / Your best / Rank*.
7. **(If using roster)** upload `roster.csv` to the **keys dataset repo**
   (hf.co/datasets/<you>/bazario-l16-keys → Add file), then restart the Space
   (Settings → Factory rebuild not needed — Restart is enough; roster is read per submission).
   Test: unknown ID → "not on the course roster".
8. **Clear the acceptance-test state**: in the **state dataset repo**, edit
   `state.json` → `[]`, delete `submissions/` folder. (Else testuser tops the board.)
9. **Lock the token down** (recommended): create a fine-grained token with *read* on
   `bazario-l16-keys` + *write* on `bazario-l16-state` only; Space Settings →
   Variables and secrets → replace `HF_TOKEN`; Restart.
10. **Keep-warm**: the Space sleeps after 48 h idle (~1 min cold start). During the
    active week, open the page (or submit once) at least every second day.

## Phase 3 — release to students (end of W8L16 lecture)

11. **Announce on Moodle/UniHub**:
    - the Space URL (direct link is fine even though the Space is private — visitors
      can *use* it, only the code/settings stay hidden);
    - the brief: `2026/code/W8L16. Introduction to Deep Learning/LEADERBOARD.md`
      (already in their forks/public export);
    - templates in the same folder — "copy, keep DO-NOT-CHANGE cells, work in YOUR WORK cells";
    - deadline: **start of W9L17** (one week), late submissions unscored.
12. **In class** (5 min): demo one live submission end-to-end on the projector —
    the format lock + score chips + rate limit make it self-explanatory after that.

## Phase 4 — while it runs (watch, don't touch)

13. Monitor the state dataset repo (submissions + `state.json`) — no server access needed.
14. Questions to expect: "rejected: row 0 date must be…" → they edited the locked cell or
    sorted the CSV — point them back to the template's save cell.
15. Remind once mid-week: **public board = half the holdout; final = other half** — don't
    tune against the visible score (it's in the rules card, worth saying out loud).

## Phase 5 — deadline & debrief (start of W9L17)

16. **Freeze**: Space Settings → secrets → add `REVEAL_PRIVATE` = `1` → Restart.
    The leaderboard tab now shows **final standings** (private half), labeled as final.
17. **Pull the evidence**: clone the state repo:
    ```bash
    git clone https://huggingface.co/datasets/<you>/bazario-l16-state state-l16
    ```
18. **Top-3 review**: for each top student — their fork notebook (commit `submit: w8l16`)
    must reproduce their best audit CSV exactly (seeded). Non-reproducible → struck.
19. **Debrief numbers** (per student / overall):
    ```bash
    $PY private/tools/score_l16.py --scan state-l16/submissions
    ```
    Race-day vs non-race RMSE + per-segment RMSLE = the "who found it" slides.
20. **Debrief deck**: walk through `private/generators/generate_l16_competitions.py`
    (F1 calendar incl. Vegas-Saturday + Gulf weighting; 11.11/Black Friday stacking;
    resellers + dead-zone + VIP×discount), show the two l16_*.png plots, reveal
    `app_cohort_segments_truth.csv`. Detective bonus (+3) to those who documented
    the discovery *before* the deadline.
21. **Grade**: best-in-class = 15 pts, baseline = 5, log-linear between (per comp),
    per the brief.

## Phase 6 — after the term

22. Next cohort: pick a new seed → Phase 1 step 1 regenerates everything → old
    submissions silently stop matching → re-deploy with `--sync` (step 5).
    Optionally delete the old state repo to archive the audit trail first.

## Quick troubleshooting

| Symptom | Fix |
|---|---|
| Space build fails | check Space → Logs; usually secrets missing or README front matter not uploaded |
| 500 on submit | `HF_TOKEN` secret lacks state-repo write scope (step 9 too strict) |
| "not on the roster" | roster.csv missing that ID — fix in keys repo, no restart needed |
| Cold start slow | normal after 48 h idle; wakes on first visit |
| Public/private flipped early | `REVEAL_PRIVATE` env — set back to 0 and restart (state is unaffected) |
