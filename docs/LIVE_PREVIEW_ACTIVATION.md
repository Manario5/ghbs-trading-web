# Live Preview / Scout / Analyze Activation (Release Train D)

The preview endpoints run the **frozen** engine logic (classifier, regime,
sizing, chandelier — read-only use, unchanged code) against live market data.
They never write to a production DB and never execute trades
(`verify_no_execution_side_effects()` guards every call).

## Endpoints
| Endpoint | Gate |
|---|---|
| `GET /api/live-preview/readiness` | none (visibility, config-only) |
| `GET /api/live-preview/sample-format` | none (static sample, no engine run) |
| `POST /api/live-preview/analyze/{ticker}` | `ENABLE_LIVE_ANALYZE_PREVIEW` + market-data gates |
| `POST /api/live-preview/scout` | `ENABLE_LIVE_SCOUT_PREVIEW` + market-data gates |

## Required flags for activation (all default false)
```
ENABLE_LIVE_ANALYZE_PREVIEW=true    # for analyze
ENABLE_LIVE_SCOUT_PREVIEW=true     # for scout
ENABLE_MARKET_DATA_SMOKE_TESTS=true
ENABLE_OHLCV_DIAGNOSTICS=true
```
Plus safety conditions checked by `/live-preview/readiness`:
- `ALLOW_PRODUCTION_DB=false`
- `DB_PATH` pointing at the test ledger

## Activation procedure (VPS)
1. Confirm baseline: `GET /api/system/safety-matrix` → SAFE.
2. Check `GET /api/live-preview/readiness` → note the exact blockers listed.
3. Edit `.env`, set the four flags above; restart the backend service.
4. Re-check readiness → `can_run_analyze_preview: true`.
5. Run previews from the UI (Analyze / Scout pages). Safety Matrix will show
   WARNING while preview flags are on — this is expected and correct.
6. When finished, restore all four flags to `false`, restart, verify SAFE.

## Guarantees
- No production DB writes (previews store results in `live_preview_runs`
  inside the test ledger only).
- No trade execution paths are reachable from preview code.
- Strategy calculations are the frozen V7.2.1 logic — Train D changed none of it.
