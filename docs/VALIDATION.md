# Validation Process (Release Train B)

## One-command validation
```bash
bash scripts/run_full_validation.sh
```
Runs, in order: full backend test suite → explicit negative safety tests →
frontend production build → secret scan. Fails fast, exits non-zero on any failure.

## Environment setup
```bash
pip install -r requirements-webapp.txt   # web-app + test deps only
npm ci
```
`requirements-webapp.txt` deliberately excludes engine-research packages
(e.g. pandas-ta) that are not needed to run or validate the FastAPI backend
and may not install on all Python versions.

## Test configuration
- `pytest.ini` sets `asyncio_mode = auto` so the async tests in
  `test_core.py`, `test_phase6u.py`, etc. run natively (they previously
  failed when `pytest-asyncio` was absent).
- Test paths are pinned to `backend/tests`.
- The env-restore fixture in `conftest.py` isolates every test's os.environ changes.

## Secret scan
`python scripts/secret_scan.py` scans all git-tracked files for
Anthropic-key, Telegram-token, generic assigned-secret, and private-key
patterns. Known-fake test fixtures are allowlisted by exact substring —
patterns are never loosened. Exit 0 = clean.

## Rules
- Never weaken a safety test to make it pass; fix the code or escalate.
- New features must ship with negative tests (locked-by-default proofs).
- Run the full validation script before every commit that will be pushed.
