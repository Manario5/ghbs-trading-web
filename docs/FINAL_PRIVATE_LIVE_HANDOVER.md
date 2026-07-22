# Final Private Live Handover

GHBS Trading — TASI Quant Command Center, moved from UAT into a polished
**private live** web app. Branch: `claude/private-live-command-center`
(from `9ab901f`, tag `uat-live-ui-fixes-approved`). Not merged, not tagged.

## What shipped
- **Operating-mode model** (`backend/core/operating_mode.py`) + `GET /api/system/operating-mode`:
  PRIVATE LIVE / AUTOMATED ALERTS / LOCKED-MAINTENANCE / RESTRICTED, with
  capabilities and guaranteed-locked invariants.
- **Read-only dashboard endpoints**: `/dashboard/charts`, `/provider-health`,
  `/alert-activity`, `/scout-funnel`, `/live-summary` — all safe empty states.
- **Redesigned Dashboard** (Command Center): operating-mode panel, risk snapshot,
  8 operational charts (regime trend, setup distribution, scout funnel, symbol
  strength, alert activity, provider health, live preview outcomes, live operations).
- **Reusable dependency-free SVG charts** (`src/components/charts/Charts.tsx`).
- **Private Live labels** replacing "Sandbox" across sidebar, topbar, Dashboard,
  Alerts, Market Data, Analyze, Scout, Settings, Login (dynamic `ModeBadge`).
- **Live Operations panel** in Alert Center.
- **Docs & profile**: `.env.live.example`, `PRIVATE_LIVE_OPERATING_MODE.md`,
  `PRIVATE_LIVE_PROFILE.md`, `DASHBOARD_CHARTS.md`, `LIVE_OPERATIONS_RUNBOOK.md`,
  this handover.

## Guarantees (unchanged, enforced)
- Trade execution / broker execution: **impossible** (no order path exists).
- Production DB write: **impossible** (`ALLOW_PRODUCTION_DB=false`, read-only gate).
- Live previews: **read-only** (frozen V7.2.1 engine, used read-only).
- Public exposure: **blocked** at the network layer (Tailscale-only).

## Validation (this branch)
- Full backend tests: **151 passed**.
- Negative-safety subset: **103 passed**.
- Frontend build: green. Secret scan + extended secret scan: clean.
- `run_full_validation.sh`: PASSED.
- Frozen strategy files vs baseline: **no diff**.

## Manual VPS deployment
1. Clone/fetch the branch into a fresh sandbox folder; do not overwrite the running one.
2. Copy `.env` from the current runtime (never from git). To go live, apply the
   `.env.live.example` gates (keep `ALLOW_PRODUCTION_DB=false`,
   `PRODUCTION_DB_READONLY_REQUIRED=true`).
3. `pip install -r requirements-webapp.txt && npm ci && npm run build`.
4. `bash scripts/run_full_validation.sh`.
5. Point systemd at the folder; restart. Verify `GET /api/system/operating-mode`
   and `GET /api/system/safety-matrix`.

## Manual browser retest checklist
- Tab title reads "GHBS Trading — TASI Quant Command Center".
- Sidebar/topbar badge reads PRIVATE LIVE (live gates on) or LOCKED / MAINTENANCE (all off).
- Dashboard: operating-mode panel + charts render; empty charts show clean empty states.
- Alert Center: Live Operations, Telegram Readiness, Scheduler Readiness panels load;
  scheduler buttons disabled when `ENABLE_ALERT_SCHEDULER=false`.
- Market Data / Analyze / Scout: mode badge shown; previews are read-only.
- Login page shows "Private Live · Authorized Access Only", no "Sandbox".
- App unreachable from the public internet.

## Still impossible (by design)
Trade execution · broker execution · production DB writes · public exposure.
