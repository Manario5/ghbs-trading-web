# Manual Sandbox Test Guide

This guide details the step-by-step process for verifying that the TASI Ledger sandbox environment works end-to-end without touching production components.

## Prerequisites
- Run local frontend server (`npm run dev`)
- Run local backend server (`python -m uvicorn backend.main:app --reload`)
- Ensure `.env` specifies `ALLOW_PRODUCTION_DB=false` (or does not exist, leaving default as securely false).

## Step-by-Step Scenario

### 1. Dashboard Load
- Navigate to `/dashboard`
- **Verify**: The "⚡ SANDBOX MODE" tag must be clearly visible next to the "Dashboard Overview" title.
- **Verify**: "Total Equity", "Cash", "Open Positions" should reflect simulated data from `tasi_ledger_test.db` (usually $100,000 for a fresh sandbox reset).

### 2. Scout Mock Run
- Navigate to `/scout`
- Click **"Run Scout Routine"**
- **Verify**: Wait for loading states to complete. Rows of mocked trading setups should appear.
- **Verify**: Hover over any row to confirm "Ticket", "Plan", "Watch", "Ignore" buttons render dynamically.

### 3. Analyze Mock Ticker
- Navigate to `/analyze`
- Enter a ticker (e.g. `2222`) and submit.
- **Verify**: "Analyze" title shows the SANDBOX text.
- **Verify**: A breakdown of the ticker's simulated fundamentals/technicals appears alongside a buy proposal.

### 4. Create Sandbox Buy Ticket
- In `/analyze` or `/scout`, click **"Create Sandbox Buy Ticket"** (or just "Ticket").
- A modal window should pop up securely warning that it's a "Simulation".
- Enter the shares.
- Click "Execute Simulation Trade".
- **Verify**: You should see a success toast/alert.

### 5. View Sandbox History & Portfolio
- Navigate to `/portfolio`
- **Verify**: The new ticker is listed as an open position.
- Navigate to `/history`
- **Verify**: The execution is listed as a `BUY` transaction.
- **Verify**: Click "Export CSV" to successfully download the sandbox transaction CSV locally. Ensure it has rows correlating with the `/history` display.

### 6. Add Action Plan Item
- From `/scout`, find an actionable item.
- Click **"Plan"** or **"Watch"**.
- Navigate to `/action-plan`.
- **Verify**: The item is queued.
- **Verify**: It has the accurate "SANDBOX MODE" alert above the list.

### 7. Cancel Action Plan Item
- On the `/action-plan` page, click the trash can icon next to the item.
- **Verify**: The item is removed.
- **Verify**: Confirm this explicitly does not delete any real trade or journal records (checked via `/journal` and `/portfolio`).

### 8. Add Journal Note
- Navigate to `/history`.
- Click **"Note"** explicitly on the recently placed `BUY` transaction.
- Add a hypothetical post-trade lesson.
- Save.
- Navigate to `/journal`.
- **Verify**: The lesson appears perfectly.

### 9. Confirm No Real Impact 
- Terminate the frontend process.
- Look at the working directory using `ls -la`.
- **Verify**: `tasi_ledger.db` does NOT exist in the workspace, or if it does, `stat tasi_ledger.db` confirms its last modified timestamp hasn't changed.
- **Verify**: `tasi_ledger_test.db` explicitly has a recently updated timestamp.

### 10. Audit Log Inspection
- (Optional) Use `sqlite3 backend/tasi_ledger_test.db "SELECT * FROM audit_log;"`
- **Verify**: Rows exist indicating "Mock Buy Position Created".

---
**End of Sandbox Test Guide.**
