# Dashboard Charts

All dashboard charts are **read-only**. They query existing SQLite tables only,
never call external providers, never run the engine, and never write data. When
a source table is empty they render a clean empty state — no fake values.

## Backend endpoints (read-only)
| Endpoint | Source | Empty-state behavior |
|---|---|---|
| `GET /api/dashboard/charts` | `setup_log`, `live_preview_runs`, `alert_events` | per-section `available:false` + message |
| `GET /api/dashboard/provider-health` | env config only | always available (config) |
| `GET /api/dashboard/alert-activity` | `alert_events` | `available:false`, empty `series` |
| `GET /api/dashboard/scout-funnel` | latest `live_preview_runs` (scout) | `available:false`, empty `stages` |
| `GET /api/dashboard/live-summary` | `system_state`, `positions`, `alert_events`, `live_preview_runs` | nulls / "None yet" |

## Charts
1. **Market Regime Trend** — line; avg regime score per day from `setup_log.market_regime`.
2. **Setup Signal Distribution** — donut; counts by `setup_log.setup_type`.
3. **Scout Funnel** — funnel; latest scout run: scanned → eligible → blocked → failures → top candidates.
4. **Symbol Strength Ranking** — horizontal bars; top symbols by avg confidence.
5. **Risk / Exposure Snapshot** — stat cards; equity, open positions, heat %, exposure (empty when not marked).
6. **Alert Activity Timeline** — bars; alerts per day (manual + scheduled, sent + failed).
7. **Provider Health** — status cards; yfinance / TwelveData / Sahmk / TradingView (configured/ready/missing/locked).
8. **Live Preview Outcomes** — bars; analyze/scout previews, alerts generated, and **trade executions = always 0 (impossible)**.

## Frontend
Reusable dependency-free SVG components in `src/components/charts/Charts.tsx`
(`LineChart`, `BarChart`, `HBarChart`, `Funnel`, `Donut`, `ChartCard`,
`EmptyState`). No external chart library, so the strict offline/CSP constraints
are respected. Mock data appears only in tests, never in the production UI.
