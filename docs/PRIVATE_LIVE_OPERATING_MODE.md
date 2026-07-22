# Private Live Operating Mode

GHBS Trading — TASI Quant Command Center runs as a **private live web app**,
not a sandbox. Operating mode is derived (read-only) from environment gates by
`backend/core/operating_mode.py` and exposed at `GET /api/system/operating-mode`.

## Modes

| Mode | Business label | When | Enabled | Always blocked |
|---|---|---|---|---|
| `PRIVATE_LIVE` | PRIVATE LIVE | Any live data / preview / manual-Telegram gate on, scheduler off | Market data, quote tests, OHLCV, provider readiness, coverage scan (if on), live Analyze/Scout preview (read-only), Anthropic readiness, manual Telegram, test-send, alert log, scheduler readiness panel | Trade/broker execution, production DB write, public exposure |
| `AUTOMATED_ALERTS` | AUTOMATED ALERTS | `ENABLE_ALERT_SCHEDULER=true` | Scheduled alert jobs, dry-run or approved sends, alert log | Trade/broker execution, production DB write, public exposure |
| `LOCKED_MAINTENANCE` | LOCKED / MAINTENANCE | All live gates off | Read-only status/readiness views only | Everything external |
| `RESTRICTED` | RESTRICTED | A dangerous condition present (prod DB write path / active execution) — should never occur | — | — |

Sub-labels used in the UI: **PRIVATE LIVE**, **LIVE READ-ONLY** (previews),
**LIVE-UAT** (safety-matrix WARNING), **AUTOMATED ALERTS**, **LOCKED / MAINTENANCE**.
"Sandbox DB" wording is used **only** when referring to `DB_PATH=tasi_ledger_test.db`.

## Guarantees (surfaced by the Operating Mode panel)
- **Trade execution / broker execution: impossible** — no order path exists.
- **Production DB write: impossible** — `ALLOW_PRODUCTION_DB=false`, read-only gate required.
- **Live previews: read-only** — engine logic (frozen V7.2.1) is used read-only.
- **Public exposure: blocked** at the network layer (Tailscale-only).

## Enabling / disabling
See `.env.live.example` and `docs/PRIVATE_LIVE_PROFILE.md`. Change gates only in
the VPS `.env`, then restart the backend. To return to locked mode, set every
`ENABLE_*` gate to `false`.
