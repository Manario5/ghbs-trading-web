# Phase 6E: Live Preview Filters + Candidate Ranking — Read-Only

## Overview
Phase 6E introduces read-only filtering, sorting, and candidate ranking directly into the Live Scout Preview interface. This functionality enables engineers and analysts to better evaluate data and setup types returned from live OHLCV queries without executing any strategy or persistence operations.

## Deliverables & Files Changed

### 1. Backend Ranking & Filtration Audit Loop (`backend/api/live_preview.py`)
- We upgraded the `POST /api/live-preview/scout` endpoint to accept an optional `filters` JSON structure to trace user parameters dynamically.
- Deployed a zero-impact display-only scoring system calculating `candidate_score`, `score_components`, `rank`, and `review_bucket` isolating data parameters:
  - Base priority on Universe tiers.
  - Signal metrics assigning weights to BUY vs HOLD.
  - Breakout setups receiving priority ranking.
  - Volume surges and ADX values scaled gracefully up to a limit.
  - Penalties for data quality warnings or failures dynamically scaling ranks.
- Configured real-time array sorting returning highest-priority candidates organically sequentially mapped via index (`rank`).
- Enforced storing requested filters within `live_preview_runs` as `"filters_applied"` for audit playback ensuring downstream tracing of data-mined subsets natively.

### 2. Frontend Filtration Toggles (`src/pages/Scout.tsx`)
- Surfaced intuitive toggle selectors parsing arrays by Sector, Tier, Data Quality, Setup Type, and Signal safely decoupling DOM mappings organically mapping to visual arrays vs database lists directly.
- Implemented quantitative bounding toggles `Show only BUY candidates` and `Top N` input filtering.
- Extended the Data Grid mapping dynamic metrics explicitly marking fields visually:
  - `Rank`
  - `Score` (`candidate_score`)
  - `Review Bucket`
- Constructed a prominent warning indicator banner denoting that Candidate scores remain read-only metrics isolating review operations securely bypassing real-world persistence logic directly preserving `sandbox_only` status completely.

## Technical Safeguards Assured
- **Display-Only Context**: Rank models are strictly embedded into JSON return payloads decoupling persistence engines completely isolating Chandelier and execution routes successfully limiting output capabilities dynamically.
- **Auditable Filtration**: The underlying logic logs the UI states dynamically writing out user queries dynamically mapped to `live_preview_runs` safely parsing logs avoiding data corruption natively maintaining constraints.

## Operational Test Workflow (VPS)
1. Run "Live Scout Preview" mapping Universe datasets.
2. Select target constraints in the UI:
   - Signal: BUY
   - Tier: TIER_1
   - Data Quality: OK
3. Observe live table components rendering matching constraints mapping `Review Bucket` fields dynamically updating outputs directly limiting elements visually safely without triggers or database execution logic.
4. Check Audit logs for recent run and verify `filters_applied` mappings accurately preserve the filter constraints within `payload_json`.

## Retest Insights & Fixes (VPS)
- Fixed an issue where the `Setup Type` filter within Live Scout Preview utilized static mismatched placeholders resulting in broken filter routes. The dropdown now leverages a dynamic set dynamically aggregating explicit `setup_type` variables directly from the result payload (e.g., `BREAKOUT_SETUP` or `MIXED_SIGNAL`).
- Replaced the placeholder `alert()` upon Audit Log `Details` clicks. Now instantiates a dynamic read-only modal actively requesting `GET /api/live-preview/runs/{id}`, surfacing tracking numbers alongside properly formatted internal settings, limits, filters, and rendering parsed JSON objects while omitting unsafe endpoints natively.
- Added explicit visual boundaries tracing `score_components` internally mapping the dynamic scores into the ScoutRow Details grid visibly labeled "Display-only score components" avoiding output assumptions securely mapping the criteria dictating candidate rank priority visually.
