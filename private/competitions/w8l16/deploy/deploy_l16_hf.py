"""One-command Hugging Face deployment for the W8L16 leaderboard site.

Creates two private dataset repos (keys, state) and one private Docker Space,
uploads the files, sets the Space secrets, and returns the URLs.

  # 1. check everything locally (no network):
  python deploy_l16_hf.py --dry-run

  # 2. deploy (reads your token; keeps repos PRIVATE):
  python deploy_l16_hf.py --username <your-hf-username> --token hf_...

  # refresh snapshots + redeploy after regenerating data:
  python deploy_l16_hf.py --username <you> --token hf_... --sync

Live sources (always re-read, snapshots in this folder are just for review):
  app code        private/tools/leaderboard_site/
  key files       private/homework_keys/{daily_orders_hidden90.csv, app_cohort_test_truth.csv}
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]                       # private/competitions/w8l16/deploy -> repo root
SITE = ROOT / "private" / "tools" / "leaderboard_site"
KEYS = ROOT / "private" / "homework_keys"

SPACE_FILES = ["app.py", "config.py", "scoring.py", "store.py", "Dockerfile",
               "requirements.txt", "README.md"]
SPACE_DIRS = ["templates", "static"]
KEY_FILES = ["daily_orders_hidden90.csv", "app_cohort_test_truth.csv"]
STATE_REPO_STUB = "This repo stores the leaderboard state (state.json) and the audit\nsubmissions. Created and maintained automatically by the Space."


def sync_snapshots() -> None:
    """Refresh space/ and keys-repo/ from the live sources."""
    space = HERE / "space"
    space.mkdir(exist_ok=True)
    for f in SPACE_FILES:
        shutil.copy2(SITE / f, space / f)
    for d in SPACE_DIRS:
        dst = space / d
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(SITE / d, dst,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    keys = HERE / "keys-repo"
    keys.mkdir(exist_ok=True)
    for f in KEY_FILES:
        shutil.copy2(KEYS / f, keys / f)
    stub = HERE / "state-repo"
    stub.mkdir(exist_ok=True)
    (stub / "README.txt").write_text(STATE_REPO_STUB, encoding="utf-8")
    print(f"synced space/ ({len(SPACE_FILES)} files, dirs: {', '.join(SPACE_DIRS)}), "
          f"keys-repo/ ({len(KEY_FILES)} files), state-repo/ stub")


def dry_run() -> bool:
    ok = True
    space = HERE / "space"
    for f in SPACE_FILES:
        if not (space / f).exists():
            print(f"MISSING space/{f}"); ok = False
    for d in SPACE_DIRS:
        if not any((space / d).iterdir()):
            print(f"MISSING space/{d}/ contents"); ok = False
    fm = (space / "README.md")
    if fm.exists() and not fm.read_text(encoding="utf-8").startswith("---"):
        print("space/README.md lacks HF front matter"); ok = False
    for f in KEY_FILES:
        p = HERE / "keys-repo" / f
        if not p.exists():
            print(f"MISSING keys-repo/{f}"); ok = False
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            n = sum(1 for _ in csv.reader(fh)) - 1
        expect = 90 if "daily_orders" in f else 600
        if n != expect:
            print(f"keys-repo/{f}: {n} rows, expected {expect}"); ok = False
    if not ok:
        print("dry-run FAILED - run --sync first")
    return ok


def upload_data_repos(token: str, username: str | None = None,
                      keys_name: str = "bazario-l16-keys", state_name: str = "bazario-l16-state") -> tuple[str, str]:
    """Create/refresh the two PRIVATE dataset repos (keys + state stub). Host-agnostic:
    used by both the HF-Space path and the Render path (state lives on HF either way)."""
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    username = username or api.whoami()["name"]
    keys_repo, state_repo = f"{username}/{keys_name}", f"{username}/{state_name}"
    for repo_id in (keys_repo, state_repo):
        api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(folder_path=str(HERE / "keys-repo"), repo_id=keys_repo,
                      repo_type="dataset", commit_message="refresh keys (cohort seed 2026)")
    api.upload_folder(folder_path=str(HERE / "state-repo"), repo_id=state_repo,
                      repo_type="dataset", commit_message="state repo stub")
    print(f"keys repo up to date:  https://huggingface.co/datasets/{keys_repo}")
    print(f"state repo up to date: https://huggingface.co/datasets/{state_repo}")
    return keys_repo, state_repo


def deploy(username: str, token: str, space_name: str, keys_name: str, state_name: str) -> None:
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    if not username:
        username = api.whoami()["name"]
        print(f"username inferred from token: {username}")
    keys_repo = f"{username}/{keys_name}"
    state_repo = f"{username}/{state_name}"
    space_repo = f"{username}/{space_name}"

    for repo_id in (keys_repo, state_repo):
        api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
        print(f"dataset ready (PRIVATE): {repo_id}")
    # The Space itself must be PUBLIC: HF gates a private Space's app URL to
    # the owner, so students could not use it. Safe by design: no secrets live
    # in the code (token/keys/state all injected at runtime), and the split
    # seed that would reveal the public/private rows is a Space secret.
    api.create_repo(repo_id=space_repo, repo_type="space", private=False,
                    space_sdk="docker", exist_ok=True)
    print(f"space ready (PUBLIC app, private data):  {space_repo}")

    api.upload_folder(folder_path=str(HERE / "keys-repo"), repo_id=keys_repo, repo_type="dataset")
    api.upload_folder(folder_path=str(HERE / "state-repo"), repo_id=state_repo, repo_type="dataset")
    print("uploaded keys + state stub")

    # secrets BEFORE pushing app files so the first build already has them
    secrets = [("HF_TOKEN", token),                 # fine-grained read-keys/write-state token recommended
               ("KEYS_REPO", keys_repo),
               ("STATE_REPO", state_repo),
               ("WINDOW_CAP", "5"),
               ("WINDOW_MINUTES", "15"),
               ("SPLIT_SEED", "2026")]              # cohort seed - stays secret (public Space code must not reveal the split)
    for k, v in secrets:
        api.add_space_secret(repo_id=space_repo, key=k, value=v)
    print(f"secrets set: {', '.join(k for k, _ in secrets)}")

    api.upload_folder(folder_path=str(HERE / "space"), repo_id=space_repo, repo_type="space")
    print(f"\nDeployed. Once the Space builds (~2-3 min):")
    print(f"  app (share this): https://{username.lower()}-{space_name}.hf.space")
    print(f"  space page:       https://huggingface.co/spaces/{space_repo}")
    print(f"  keys repo:        https://huggingface.co/datasets/{keys_repo}  (add roster.csv here, then RESTART the Space)")
    print(f"  state repo:       https://huggingface.co/datasets/{state_repo}  (audit trail)")


def _token_from_env_or_dotenv() -> str | None:
    import os
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", help="HF namespace (default: inferred from the token)")
    ap.add_argument("--token", help="HF token with write access (or HF_TOKEN env / .env)")
    ap.add_argument("--space-name", default="bazario-l16-leaderboard")
    ap.add_argument("--keys-name", default="bazario-l16-keys")
    ap.add_argument("--state-name", default="bazario-l16-state")
    ap.add_argument("--sync", action="store_true", help="refresh snapshots from live sources first")
    ap.add_argument("--data-only", action="store_true",
                    help="upload/refresh ONLY the keys+state dataset repos (Render path); no Space")
    ap.add_argument("--deploy", action="store_true", help="deploy the HF Space (needs HF PRO for Docker)")
    ap.add_argument("--dry-run", action="store_true", help="local checks only, no upload")
    args = ap.parse_args()

    if args.sync or not (HERE / "space" / "app.py").exists():
        sync_snapshots()
    if args.dry_run:
        sys.exit(0 if dry_run() else 1)
    if args.data_only:
        token = args.token or _token_from_env_or_dotenv()
        if not token:
            ap.error("no token for --data-only (pass --token / HF_TOKEN / .env)")
        upload_data_repos(token)
        sys.exit(0)
    if not args.deploy:
        print("Snapshots are up to date. (pass --deploy to push to HF, --data-only for"
              " keys/state refresh only, --dry-run to check)")
        sys.exit(0)
    token = args.token or _token_from_env_or_dotenv()
    if not token:
        ap.error("no token: pass --token, set HF_TOKEN, or put HF_TOKEN=... in the repo root .env")
    deploy(args.username, token, args.space_name, args.keys_name, args.state_name)
