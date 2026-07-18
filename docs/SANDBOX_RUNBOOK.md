# Sandbox Local/VPS Runbook

This guide covers setting up the TASI AI Trading System specifically for isolated Sandbox QA on a Local Machine or VPS. By following this guide, you guarantee absolutely no contact with real execution algorithms, external webhooks, or production storage paths.

## Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **npm** or yarn

## 1. Environment Configuration Setup
Create a `.env` file in the root directory based on `.env.example`.

**Mandatory `.env` configuration:**
```env
# Database Protection
ALLOW_PRODUCTION_DB=false
DB_PATH=tasi_ledger_test.db

# Authentication
JWT_SECRET_KEY=change_me_for_sandbox
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Client Configuration
VITE_API_URL=http://localhost:8000
```
*Verify `ALLOW_PRODUCTION_DB=false` is explicitly set.*

## 2. Backend Initialization
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the Sandbox Database. The backend will automatically generate the schema over `tasi_ledger_test.db` when FastAPI launches.
   
4. Start FastAPI server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.0 --port 8000
   ```
   *Terminal Output Verification: Ensure there are no outputs attempting to attach to `tasi_ledger.db`.*

## 3. Frontend Initialization
1. In a separate terminal, install node packages:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Terminal Output Verification: The server should expose itself over `http://localhost:3000` (or `5173`).*

## 4. Sandbox Setup & Login
When you start the backend with `ALLOW_PRODUCTION_DB=false`, it will automatically seed a sandbox admin user if it does not already exist.

Use the following credentials to log in:
- **Username:** `sandbox_admin`
- **Password:** `SandboxTest123!`

## 5. Security & Verification Commands
Run the following in the project root to guarantee structural safety:
- **String Check**: `grep -rn "tasi_ledger.db" src/` *(Must return nothing)*
- **Frontend Verify**: `npx tsc --noEmit && npm run build`
- **Backend Tests**: `python -m pytest backend/tests -q` *(You must run this in your localized Python environment before progressing to later phases)*

## 6. Safe Shutdown Sequence
1. Standard `CTRL+C` on the backend running `uvicorn`.
2. Standard `CTRL+C` on the frontend running `vite`.
3. If necessary, you can safely delete the `tasi_ledger_test.db` file to completely wipe the mock history before your next run.
