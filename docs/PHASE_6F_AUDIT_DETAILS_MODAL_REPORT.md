# Phase 6F: Audit Log Details Modal + Structured Trace Viewer

## Overview
Phase 6F refactors the user interface for viewing Live Preview audit logs. The prior implementation displayed raw JSON and tracking values that were hard to read for analysts or non-developer roles. The new solution parses payloads safely to generate a clean, structured trace dashboard directly within the application while maintaining a fully sandbox-compliant (read-only) execution envelope.

## Deliverables & Files Changed

### `backend/api/live_preview.py`
- Upgraded the `/api/live-preview/runs/{run_id}` endpoint.
- Implemented payload normalization parsing raw JSON artifacts into standard attributes explicitly grouping fields: `id`, `event_type`, `summary`, `filters_applied`, and an array of `candidates`.
- Ensured graceful error trapping catching `JSONDecodeError` and type coercion failures. All outputs map correctly, even with historically corrupt log entities ensuring forward-compatibility with missing payload constraints natively.
- No modifications were applied to the trading engine or signal evaluation pipelines guaranteeing strategy logic stability organically.

### `src/pages/Analyze.tsx`
- Decoupled the raw JSON visualization dumping payloads openly against modals natively.
- Implemented an immersive Dashboard view modal leveraging `<details>` for advanced raw outputs explicitly segregating meta insights (e.g. Actionable triggers, Tiers, Segments).
- Bound metrics seamlessly utilizing chips natively tagging indicators (e.g. `BUY`, `SELL`, `HOLD`) dynamically allocating clear intent mapping signals organically mapping to underlying backend shapes accurately.
- Retained strict sandbox constraints natively limiting outputs rendering purely quantitative summaries avoiding implicit strategy overrides.

## Testing Insights (VPS Readiness Validated)
- Executing `python -m pytest backend/tests -q` completes successfully confirming backend structural shifts have not crippled trading endpoints.
- Typescript build completed successfully demonstrating typing and structure integrity.
- Verified visual details confirming "Actionable" tags respect the `mechanical_actionable` triggers from Phase 6E explicitly bounding strategy paths seamlessly limiting outputs securely.
