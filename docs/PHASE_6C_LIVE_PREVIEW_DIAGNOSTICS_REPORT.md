# Phase 6C: Live Preview Signal Diagnostics + Explainability

## Overview
Phase 6C introduces transparent diagnostic metrics into both "Live Analyze Preview" and "Live Scout Preview" endpoints. This iteration surfaces previously invisible quantitative boundaries tracking exact rules triggering action (or ignoring setups natively). It respects zero-execution limits safely maintaining sandbox-only visualization without connecting to production tables, logging routines, or automated event-loops natively.

## Deliverables & Files Changed

### 1. Backend Diagnostics API (`backend/api/live_preview.py`)
- Mapped explicit variables bridging current logic variables onto REST boundaries seamlessly tracing `diagnostic_summary` components visually translating internal strings back onto API interfaces gracefully mapping current configurations directly.
- Segregated indicator outputs isolating exact calculations securely routing:
  - RSI calculations
  - ADX markers
  - BB Upper and Lower deltas
  - Moving Average convergences
- Validated thresholds output tracking exact config representations verifying what parameters define action variables accurately mapping `.env` boundaries vs strategy constants natively mitigating opaque assumptions directly.
- Deployed safe JSON sanitization explicitly filtering `NaN`, `Infinity`, or untyped `NumPy` mappings converting invalid components gracefully avoiding 500 error footprints natively isolating math boundary failures dynamically mitigating downstream UX crashing.

### 2. Frontend UI Diagnostics (`src/pages/Analyze.tsx` & `src/pages/Scout.tsx`)
- Constructed dynamic "Why this signal?" panels under Live Analyze Preview isolating indicators and diagnostic metrics separately rendering clear `Signal Reasons` vs `Blocking Reasons` naturally.
- Added expandable `<tr>` rows native to the Live Scout Preview allowing developers to dissect explicit signal states natively expanding tables gracefully visually exposing deeper math mechanics safely omitting action-tickets natively rendering zero execution overrides successfully mapping isolation.
- Built exact indicator visualizations formatting null parameters as explicit `N/A` text placeholders protecting UI component mapping ensuring graceful failure formatting organically.

## Technical Safeguards Assured
- **No Database Triggers**: Data diagnostics parse dynamically in memory isolating queries completely omitting production SQLite logging mechanisms bypassing persistence totally.
- **No Alert Automations**: Engine components decoupling alerts remain disconnected parsing logic visually avoiding execution states organically enforcing preview limits effectively.
- **Strict Read-Only Parameters**: Diagnostics rely exclusively on logic evaluation natively mapping arrays visualizing results rather than activating live hooks securely isolating strategy components naturally limiting production consequences successfully.

## Operational Test Workflow (VPS)
1. Verify Live Analyze Preview runs via `2222`.
2. Open "Why this signal?" panel explicitly mapping Regime, Signal, Setup, and Diagnostics confirming text mappings natively exposing string combinations (e.g. `RSI_OVERSOLD+MACD_IMPROVING`).
3. View the threshold indicators isolating actual parameters correctly converting `null` mappings to `N/A` organically validating downstream UX formats dynamically.
4. Open the Scout interface clicking "Run Live Scout Preview".
5. Observe diagnostic `Details` expansion under row outputs verifying internal mechanisms seamlessly parsing table limits verifying indicators directly.
6. Verify no trade execution, alert scheduling, or log states trigger validating test limitations securely.
