# Market Data Provider Setup (Release Train C)

All provider access is configured through VPS `.env` only. No keys in code,
no keys in git, defaults locked.

## Providers

| Provider | Key env var | Adapter | Notes |
|---|---|---|---|
| yfinance | none | implemented | default provider, no key needed |
| TwelveData | `TWELVEDATA_API_KEY` | implemented | first fallback |
| Sahmk | `SAHMK_API_KEY` | readiness only | adapter to be built when API access is purchased |
| TradingView | `TRADINGVIEW_API_KEY` | readiness only | config placeholder; TradingView has no simple public REST quote API |

Fallback order: `yfinance → twelvedata → sahmk → tradingview`.
Providers without a key or without an implemented adapter are skipped and
reported in `GET /api/market-data/provider-health` under `skipped_providers`.

## Gates (all default false)
| Flag | Unlocks |
|---|---|
| `ENABLE_MARKET_DATA_SMOKE_TESTS` | single-quote smoke tests |
| `ENABLE_OHLCV_DIAGNOSTICS` | historical OHLCV diagnostics |
| `ENABLE_PROVIDER_COVERAGE_SCAN` | universe-wide coverage scan |

With every gate false, **no network call is possible** — enforced by tests
(`test_locked_smoke_test_makes_no_network_call`).

## Configuring keys later on the VPS
1. SSH to the VPS; edit the runtime `.env` (never commit it):
   ```
   TWELVEDATA_API_KEY=<key>
   ```
2. Restart the backend service.
3. Verify masked readiness (no key values appear):
   - `GET /api/market-data/provider-health` → `twelvedata.secret_masked: "configured"`
   - UI → Market Data page → Provider Readiness panel
4. To actually test a quote, temporarily set `ENABLE_MARKET_DATA_SMOKE_TESTS=true`,
   restart, run one test from the Market Data page, then set it back to
   `false` and restart. Safety Matrix shows WARNING while enabled.
