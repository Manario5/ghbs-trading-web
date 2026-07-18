# Sandbox QA Validation Checklist

This checklist confirms that the TASI Ledger sandbox environment remains isolated, functional, and visually marked as a simulation prior to any potential production steps.

## Authentication & Access
- [ ] Login screen works and rejects bad credentials.
- [ ] Protected routes redirect unauthenticated users back to login.

## Data & Display Verification
- [ ] Dashboard page loads Mock/Simulated equity metrics.
- [ ] Account page loads accurately mapping to the Sandbox DB profile.
- [ ] Portfolio page loads with clear "No open positions" or Mock positions.

## Module Functional Rules
- [ ] **Scout Module**: Creating a mock run successfully surfaces simulated tickers and enables action buttons.
- [ ] **Analyze Module**: Passing a mock ticker strictly returns simulated risk and profile outputs.
- [ ] **Action Plan**: Adding an item successfully cascades through the pipeline correctly without backend alerts firing.
- [ ] **Action Plan**: Canceling an item successfully scrubs the simulated item.
- [ ] **Journal Module**: Adding note types triggers correct storage and loads exactly correctly via `/journal` filtering.

## Trading Workflow Isolation
- [ ] **Buy Ticket**: Opens and explicitly highlights "Sandbox Simulation".
- [ ] **Risk Preview**: Dynamically calculates simulated metrics for a ticker.
- [ ] **Execution Storage**: Resolving the Sandbox Buy immediately stores a generic record to `tasi_ledger_test.db` and updates Portfolio UI.
- [ ] **Execution History**: The generated trade is available on the `/history` screen payload.
- [ ] **Sell Ticket**: Liquidating a mock position from `/portfolio` securely updates `tasi_ledger_test.db` History and empties Portfolio.
- [ ] **Export Integrity**: Downloading the generic Sandbox history over CSV perfectly maps UI outputs to tabular files.

## Visual Sandbox Assurances
- [ ] "⚡ SANDBOX MODE" tags are strictly visible across all navigation payloads (Dashboard, Account, Portfolio, Action Plan, Journal, Scout, Analyze, History, Performance).
- [ ] Modal confirmations explicitly mandate acknowledgment of "No Live Trading" conditions.

## Strict Production Guards
- [ ] Confirmed ZERO real executed orders took place.
- [ ] Confirmed ZERO changes were written to standard algorithm modules in the backend codebase.
- [ ] Confirmed ZERO external APIs were pinged (no `yfinance`, no `Claude`, no `Telegram`).
- [ ] Checked server logs: `tasi_ledger.db` does not exist or was never queried.
