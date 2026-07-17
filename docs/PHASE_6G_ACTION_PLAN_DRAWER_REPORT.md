# Phase 6G: Action Plan Drawer

## Overview
Phase 6G introduces an Action Plan Drawer component built natively for the trading interface. Instead of modifying trading execution routines internally, this visual layer bridges "signals" generated within the sandbox directly providing an interface for manual replication using the external trading application (Derayah) + Telegram bot entry recording safely without automating triggers. 

## Files Changed
- **`src/components/ActionPlanDrawer.tsx`**
  - Synthesized a reusable React `<ActionPlanDrawer />` component displaying structured trade instructions statically parsed.
  - Generates exact Telegram string payloads (e.g., `/buy 2222 <fill_price> <qty>`) wrapped in copy-to-clipboard functionality cleanly formatted into safe snippets protecting execution bounds natively.

- **`src/pages/Scout.tsx`**
  - Surfaced `Action Plan` button to the `ScoutRow` rendering components alongside the normal `Details` drop-down, passing local candidate artifacts down efficiently.

- **`src/pages/Analyze.tsx`**
  - Integrated the global `ActionPlanDrawer` onto explicit single-result "Live Preview" screens safely bounded under "Sandbox Only" rendering arrays intuitively.
  - Linked candidate parsing within the newly updated robust Audit Details tracking screens actively opening `showActionPlan` modal elements extracting merged data entities gracefully.

## UI Sections Implemented
- **Candidate Summary**: Quick context matching signal statuses, segments, regions, tiering, and overarching setup markers visibly distinct.
- **Technical Snapshot**: Maps static latest properties natively covering ADX, RSI, Volume Surges, and close relations natively.
- **Trade Plan**: Derives the entry allocations actively presenting Notional sizing metrics mapped dynamically assuming $100k internal bounds statically avoiding assumption risks (shows HOLD/SELL logic properly dropping variables).
- **Manual Execution Checklist**: Outlines hard constraints preventing rushed behaviors surfacing checklists prior safely enforcing Derayah routines organically.
- **Telegram Command Helper**: Aggregated strings cleanly prepared for quick copying dynamically filling in Ticker and Quantity properties accurately mapped to existing payloads.

## Constraints & Confirmations
- Did **NOT** change system routines organically automating payloads.
- Kept **ALL** database transactions explicitly locked out. Action Plan simply structures output JSON values distinctly making review processes seamless statically.

## VPS Issue Found & Fix Applied
During VPS testing, an issue was discovered where clicking the "Action Plan" button in the Live Data Scout Preview incorrectly opened the "Add Sandbox Plan Item" modal and initiated a call to the backend Action Plan API resulting in data mutation in SQLite.

**Root Cause:**
The `Scout.tsx` component was incorrectly utilizing the `handleActionPlan()` method (which triggers a `POST /action-plan`) for the Live Data Preview. The existing mock Action Plan logic overlapped with the newly expected read-only Drawer intent.

**Fix Applied:**
- Modified `src/pages/Scout.tsx` so the "Action Plan" button in `ScoutRow` now explicitly toggles `setShowActionPlan(true)` instead of invoking `handleActionPlan(...)`.
- Modified `src/pages/Analyze.tsx` to similarly enforce standalone isolation for the Live Data Preview view.
- Preserved existing mock functionality exclusively where it was already safely applied.

**Confirmations:**
- Live Preview Action Plan is strictly **read-only**.
- Live Preview Action Plan **does not** create Tomorrow Action Plan items.
- Live Preview Action Plan **does not** call any Telegram, broker, or backend execution APIs.

## VPS Retest Issue Found & Fix Applied
During the VPS Retest, another issue was surfaced inside the Telegram Command Helper.
The baseline `navigator.clipboard.writeText()` implementation occasionally fails on non-HTTPS environments when served over HTTP/IP natively blocking clipboard execution access seamlessly, breaking the core requirements directly.

**Fix Applied:**
- Enhanced the `ActionPlanDrawer.tsx` `copyToClipboard()` functionality to explicitly fall back to `document.execCommand('copy')` leveraging a hidden `<textarea>` whenever it isn't rendered in a Secure Context.
- Broadened the Telegram Commands mapped cleanly parsing TP blocks locally allocating Take Profit segments systematically wrapping texts clearly.
- Rendered exact temporary success/failure markers natively mapping "COPIED" UI responses natively safely bound directly replacing the alert dialogue gracefully protecting UX context completely.
- Confirmed Risk Reminder banners avoid text truncation gracefully enforcing wrap styling elegantly ensuring mobile layout sanity globally.

**Confirmations:**
- Copy buttons ONLY write text locally directly mapping to the user clipboard. No Telegram messages are ever routed to the backend asynchronously.

## Validation
- Ensure `$npm run build` processes statically without TypeScript anomalies globally preserving syntax mappings natively.
- Evaluated `npx tsc --noEmit` locally bypassing regressions entirely.
