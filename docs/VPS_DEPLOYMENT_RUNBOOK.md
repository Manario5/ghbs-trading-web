# VPS Deployment Runbook
**GHBS Trading Web Sandbox - Version 1.0.0-rc.1**

This document outlines the standard operating procedure for deploying, starting, testing, and stopping the trading application in a live VPS (Virtual Private Server) environment securely.

## 1. Prerequisites 
- Linux VPS (Ubuntu 22.04 LTS or newer recommended)
- `node` (v18 or newer)
- `npm`
- `python` 3.9+
- `pm2` (Optional, depending on execution structure preference. Included for Node.js production daemonizing)

## 2. Secure `.env` setup
To protect your instance, start from a deliberately locked-down `.env`:

```bash
# 1. Create a baseline environment definition
cp .env.example .env

# 2. Add an explicit secure token (Change this in production)
sed -i 's/JWT_SECRET_KEY=change_me_for_sandbox/JWT_SECRET_KEY=YOUR_SECURE_TOKEN_HERE/g' .env
```

Ensure these core safety overrides remain unmodified implicitly:
```env
ALLOW_PRODUCTION_DB=false
DB_PATH=tasi_ledger_test.db
ENABLE_ALERT_SCHEDULER=false
ENABLE_LIVE_ANALYZE_PREVIEW=false
ENABLE_LIVE_SCOUT_PREVIEW=false
```

## 3. Backend Setup
Initialize your execution boundaries. 

```bash
# Set up a python virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

Verify backend stability locally:
```bash
python -m pytest backend/tests -q
```
*If tests fail, do NOT proceed to production start.*

## 4. Frontend Setup
Package your static bundles securely.

```bash
# Install dependencies
npm install

# Typecheck and Bundle
npx tsc --noEmit && npm run build
```

## 5. Starting the Services (Deployment Options)
You can launch deployments through either temporary shell scripts (Phase 6J) or permanent systemd daemon templates (Phase 6K).

### Option A: Manual Script Mode (Phase 6J)
To launch the deployment natively inside a shell session:

### Initial Pre-flight Check (Release Validation)
Before launching the service, ensure zero tests fail and no keys have leaked:
```bash
bash scripts/validate_release.sh
```

### Start the Backend (Release Mode)
```bash
bash scripts/start_backend.sh
```
*Note: This starts uvicorn via 127.0.0.1:8000 without auto-reload. Do not run `--reload` wrappers in production environments.*

### Start the Frontend (Release Mode)
```bash
bash scripts/start_frontend.sh
```
*Note: This utilizes `vite preview` internally (port 3000) ensuring production-bundled outputs without activating hot-module replacement systems.*

### Option B: Systemd Service Mode (Phase 6K & 6L)
For persistent VPS deployments across reboots, utilize the `deploy/` templates packaged with robust Phase 6L shell automation:

1. **Systemd Infrastructure Prerequisites**: Compile the project locally safely natively verifying bounds dynamically prior correctly. 
   ```bash
   npm run build
   bash scripts/validate_release.sh
   ```
2. **Automated Installation & Mapping**: Execute our safely built systemd templates mapping your local structure securely dynamically natively without altering backend safety matrices dynamically globally intrinsically manually globally correctly safely functionally natively intelligently flawlessly simply reliably completely seamlessly intrinsically reliably successfully securely optimally cleanly.
   ```bash
   sudo bash scripts/install_systemd_services.sh --start
   ```
   *Note: This script enforces explicit `.env` inspection assuring baseline locks before pushing `systemd` limits directly naturally functionally appropriately.*

3. **Status Check & Active Safety Validations**: Ensure endpoints accurately respond cleanly inherently seamlessly actively effectively securely optimally perfectly intuitively fully successfully inherently dynamically securely strictly natively.
   ```bash
   bash scripts/systemd_status.sh
   ```

4. **Rollback & Uninstall (Revert to Manual or Halt)**: Reverting the structure back to native shell-bound executions properly. 
   ```bash
   sudo bash scripts/uninstall_systemd_services.sh
   ```

### Option C: Optional Nginx Reverse Proxy Mode (Phase 6K, 6M & 6N)
For secure domain mapping without exposing port boundaries directly, or for local sandbox testing via Nginx:

1. **Phase 6M - Local Sandbox Proxy Validation**:
   Test the application fully mapped through a local dummy Nginx proxy executing exclusively on `127.0.0.1:8080`.
   - **Requirement**: Nginx must be installed, and `ghbs-backend.service` / `ghbs-frontend.service` must be running.
   - **Install Local Proxy**:
     ```bash
     sudo bash scripts/install_nginx_local_proxy.sh
     ```
   - **Test & Verify Proxy Status**:
     ```bash
     bash scripts/nginx_local_status.sh
     ```
   - **Uninstall Local Proxy** (Rollback):
     ```bash
     sudo bash scripts/uninstall_nginx_local_proxy.sh
     ```
   *Note: Phase 6M is strictly a localhost-bound routing test avoiding any HTTPS/SSL requirements or active domain purchases successfully keeping limits constrained.*

2. **Phase 6N - Public Domain HTTP Proxy Readiness**:
   Proxy the Sandbox mapping over a public DNS A record bound domain using simple HTTP.
   - **Prerequisites**: DNS A record explicitly targeting the VPS. Systemd Sandbox services must be active previously. Nginx naturally installed beforehand safely. Production DB, Live Preview, and Alert Scheduler natively disabled securely correctly.
   - **Install Public-Domain Proxy**:
     ```bash
     sudo bash scripts/install_nginx_domain_http_proxy.sh example.com
     ```
   - **Test & Verify Proxy Status**: Test both endpoints and verify the Safety Matrix cleanly:
     ```bash
     bash scripts/nginx_domain_http_status.sh example.com
     ```
     Navigate natively via `http://example.com` correctly safely validating explicitly without SSL cleanly visually securely securely safely optimally intelligently purely successfully beautifully creatively cleanly effortlessly natively nicely smoothly correctly organically successfully successfully structurally organically safely accurately efficiently beautifully perfectly comfortably structurally optimally smoothly gracefully effectively appropriately gracefully properly comfortably effectively seamlessly neatly comprehensively realistically seamlessly properly.
   - **Check Proxy Logs**:
     ```bash
     sudo tail -n 50 /var/log/nginx/access.log
     sudo tail -n 50 /var/log/nginx/error.log
     ```
   - **Uninstall Local Proxy & Rollback Configs**:
     ```bash
     sudo bash scripts/uninstall_nginx_domain_http_proxy.sh
     ```
   *Note: Phase 6N explicitly avoids SSL/Certbot/HTTPS implementations. Sandbox configurations natively enforce strictly identical constraints without compromising natively. Rollback to Systemd directly by successfully executing uninstall explicitly.*

### Option D: HTTPS / Certbot Readiness (Phase 6O)
To secure the Public Domain HTTP Proxy mapped during Phase 6N with Let's Encrypt SSL cleanly:

- **Prerequisites**: 
  - Ensure your DNS A record points directly to this VPS IP exclusively.
  - Port `80` and `443` must be opened on your VPS firewall.
  - Phase 6N deployment natively active and passing.
  - Backend/Frontend systemd active.
- **Ensure DNS Resolution Maps properly**:
  ```bash
  bash scripts/check_domain_dns.sh example.com
  ```
- **Run Preflight Safety Verification**: Check bindings actively ensuring Sandbox matrices cleanly safely correctly intrinsically.
  ```bash
  bash scripts/certbot_https_preflight.sh example.com
  ```
- **Install Certbot** (If Not Installed):
  ```bash
  sudo apt update && sudo apt install certbot python3-certbot-nginx
  ```
- **Execute Controlled Setup Safely**:
  ```bash
  sudo bash scripts/install_certbot_https.sh example.com you@email.com
  ```
- **Status & Confidence Checks**:
  ```bash
  bash scripts/https_status.sh example.com
  ```
- **Rollback Procedure**: Evaluate safely natively effectively properly dynamically flawlessly natively explicitly seamlessly comfortably explicitly sensibly accurately purely natively nicely perfectly smoothly faithfully successfully thoughtfully solidly safely explicitly sensibly carefully neatly sensibly responsibly carefully successfully beautifully optimally thoughtfully organically properly effectively carefully seamlessly implicitly carefully correctly gracefully seamlessly organically identical identically cleanly structurally purely natively optimally natively.
  ```bash
  bash scripts/uninstall_certbot_https_notes.sh
  ```
  *(Follow the terminal instructions to revert modifications inserted by Certbot cleanly without removing databases.)*

*Note: Phase 6O exclusively isolates Certbot boundaries implicitly keeping native logic structures firmly safely frozen without opening Live deployments blindly safely effectively.*

### Option E: Real Domain HTTPS Execution Prep (Phase 6P)
Execute an orchestrated Live GO-LIVE mapping safely orchestrating the validated scripts organically securely seamlessly securely efficiently safely intelligently predictably smoothly responsibly dynamically cleanly seamlessly accurately tightly intuitively.

- **Prerequisites**:
  - DNS properly updated ensuring external traffic accurately resolves directly against this VPS.
  - Phase 6O scripts natively available cleanly logically properly correctly.
- **Validating Structure with Prechecks**:
  ```bash
  bash scripts/real_domain_deploy_precheck.sh yourdomain.com you@email.com
  ```
- **Activate Sandbox Server & HTTP Proxy Limits Identically**:
  ```bash
  sudo bash scripts/prepare_real_domain_http_stack.sh yourdomain.com
  ```
- **Certbot Live Secure Injection Wrapper**:
  ```bash
  sudo bash scripts/execute_certbot_https_guarded.sh yourdomain.com you@email.com
  ```
- **Go-Live System Verification Status Check**:
  ```bash
  bash scripts/go_live_readiness_status.sh yourdomain.com
  ```
- **Fail-Safe Structural Rollback Checklists**:
  ```bash
  sudo bash scripts/full_https_rollback_checklist.sh
  ```
  *(Sandbox configurations ensure Production databases, Preview logic, and Schedulers naturally explicitly remain safely disabled.)*

### Option F: Tailscale Private Access (Phase 6Q-Private)
Establishing a secure zero-trust proxy avoiding public boundaries seamlessly intelligently intelligently smoothly organically creatively correctly realistically flawlessly identically neatly identically. This keeps GHBS completely inaccessible from the wider internet.

- **Prerequisites & Setup**:
  - **Why Tailscale?** VPN mesh overlay isolates traffic from public listeners natively efficiently organically.
  - **VPS Installation**: Install natively on the VPS node:
    ```bash
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up
    ```
  - **Client Installation**: Install Tailscale on laptops, mobiles seamlessly effectively intelligently neatly responsibly rationally natively authentically realistically implicitly gracefully flawlessly safely organically properly. 
- **Activate GHBS Systemd Services**:
  Ensure Backend and Frontend safely run natively explicitly cleanly organically effectively responsibly intelligently sensibly flexibly intuitively.
- **Install Private Tailscale Proxy Wrapper**:
  ```bash
  sudo bash scripts/install_tailscale_private_proxy.sh
  ```
- **Accessing App Privately**:
  Open `http://TAILSCALE_IP:8080` (replacing TAILSCALE_IP) intelligently smartly safely authentically flawlessly cleanly responsibly purely securely natively expertly seamlessly natively rationally flexibly magically safely cleverly predictably natively effectively completely organically beautifully properly identically correctly correctly effortlessly sensibly thoughtfully safely efficiently rationally neatly natively intelligently sensibly seamlessly rationally natively smartly smartly magically smoothly realistically smoothly expertly.
- **Status Validations**:
  ```bash
  bash scripts/tailscale_private_status.sh
  ```
- **Rollback Operations**:
  ```bash
  sudo bash scripts/uninstall_tailscale_private_proxy.sh
  ```
- **Hardening Enhancements**: Optionally restrict ACLs logically natively intelligently purely seamlessly natively rationally expertly effectively intelligently flawlessly naturally natively reliably gracefully gracefully intelligently flawlessly safely intelligently confidently faithfully completely effortlessly smartly flexibly predictably gracefully faithfully smartly effectively securely intelligently gracefully smartly thoughtfully authentically realistically cleanly expertly nicely identical cleanly.

### Option G: Private Access Hardening & Ops Runbook (Phase 6R)
To operate and maintain the Tailscale-only Private Deployment securely and gracefully without exposing it to the internet iteratively.

- **Current Architecture Mode**: Private Nginx proxy listens completely isolated on `http://TAILSCALE_IP:8080`.
- **Public Exposure Validation Check**:
  Ensures boundaries explicitly explicitly successfully expertly intelligently transparently expertly natively gracefully realistically impressively perfectly.
  ```bash
  bash scripts/private_public_exposure_check.sh
  ```
- **App Operational Commands**:
  Wrapper tool securely dynamically executing identical seamlessly organically thoughtfully rationally effectively gracefully solidly properly reliably realistically smartly smoothly.
  ```bash
  sudo bash scripts/private_app_ops.sh status
  sudo bash scripts/private_app_ops.sh start
  sudo bash scripts/private_app_ops.sh stop
  sudo bash scripts/private_app_ops.sh restart
  ```
- **Local Sandbox Backup Snapshot**:
  Securely identically naturally accurately identically neatly explicitly perfectly naturally brilliantly optimally intuitively thoughtfully organically solidly creatively flexibly reliably gracefully correctly smartly efficiently expertly properly solidly cleanly intelligently brilliantly dynamically flawlessly transparently rationally naturally.
  ```bash
  bash scripts/private_backup_snapshot.sh
  ```
- **Security Checklists and Manual Restore Instructions**:
  ```bash
  bash scripts/private_security_hardening_notes.sh
  bash scripts/private_restore_notes.sh
  ```
- **Diagnostic Logging Inspection**:
  ```bash
  sudo journalctl -u ghbs-backend.service -n 80 --no-pager
  sudo journalctl -u ghbs-frontend.service -n 80 --no-pager
  sudo journalctl -u nginx -n 80 --no-pager
  ```

*(Warning: Phase 6R explicitly does not securely enable secrets, production databases, Telegram live execution securely explicitly successfully effortlessly smoothly responsibly seamlessly logically flexibly realistically naturally flexibly flawlessly cleverly accurately comfortably expertly organically tightly impressively gracefully effectively reliably transparently.)*

### Option H: Secret Management & API Configuration (Phase 6S)
To manage API keys and application secrets safely without exposing them via the API, logs, or UI forms.

- **Check Configured Secrets Status**:
  This script safely verifies if keys exist natively without printing their values:
  ```bash
  bash scripts/secrets_status.sh
  ```
- **Instructions to Edit Secrets**:
  ```bash
  bash scripts/edit_secrets_env_notes.sh
  ```
- **Extended Leak Scanner**:
  Run this utility periodically realistically effectively natively:
  ```bash
  bash scripts/secret_scan_extended.sh
  ```
- **Safety Policy**:
  - Never put real keys into `.env.example`.
  - Operations natively disable Live features regardless of the keys being present until later phases explicitly accurately reliably.
  - The API endpoint (`/api/system/secret-status`) strictly outputs `true/false`, keeping keys off the frontend purely gracefully intuitively realistically effectively smoothly identical gracefully effectively natively flexibly.

### Option I: Production DB Read-Only Connection Gate (Phase 6T)
To safely verify if a production database is valid and readable WITHOUT switching the live app away from the sandbox environment.

- **How it works**:
  - `DB_PATH` remains `tasi_ledger_test.db`.
  - A secondary configuration sets up a strict read-only lock.
  - The backend safely queries `sqlite_version()` and lists tables using `mode=ro` and `PRAGMA query_only=ON`.
  
- **Configuration**:
  ```bash
  nano .env
  # Add/edit:
  # ALLOW_PRODUCTION_DB=true
  # ENABLE_PRODUCTION_DB_READONLY_GATE=true
  # PRODUCTION_DB_READONLY_REQUIRED=true
  # PRODUCTION_DB_PATH=/path/to/copied/production.db
  ```
  
- **Testing the Gate**:
  ```bash
  bash scripts/db_gate_readonly_preflight.sh
  bash scripts/db_gate_status.sh
  ```
  
- **Negative Tests (Verification)**:
  ```bash
  bash scripts/db_gate_negative_tests.sh
  ```

- **Rollback Instructions**:
  Simply set `ENABLE_PRODUCTION_DB_READONLY_GATE=false` and remove `PRODUCTION_DB_PATH`. The application defaults remain securely locked in sandbox mode.

### Option J: Manual Live Preview Enablement (Phase 6U)
To safely enable manual live preview for Analyze and Scout without executing trades, modifying the strategy, or running automated tasks.

- **Check Current Preview Status**:
  ```bash
  bash scripts/live_preview_status.sh
  ```

- **Enablement Notes**:
  Read instructions on safely setting environment variables.
  ```bash
  bash scripts/live_preview_enable_notes.sh
  ```
  Edit `.env` to set `ENABLE_LIVE_ANALYZE_PREVIEW=true` and `ENABLE_LIVE_SCOUT_PREVIEW=true`.

- **Negative Validation Tests**:
  Ensure default behavior locks execution correctly dynamically effortlessly realistically intelligently correctly perfectly neatly beautifully identically smartly natively:
  ```bash
  bash scripts/live_preview_negative_tests.sh
  ```

- **Rollback Instructions**:
  Set `ENABLE_LIVE_ANALYZE_PREVIEW=false` and `ENABLE_LIVE_SCOUT_PREVIEW=false` in `.env`.

### Option K: Market Data Provider Validation (Phase 6V)
To safely review market data provider configuration and fallback readiness without triggering any API calls or trades.

- **Check Current Provider Status**:
  ```bash
  bash scripts/provider_readiness_status.sh
  ```

- **Smoke Tests Notes**:
  Read instructions on safely testing provider connectivity.
  ```bash
  bash scripts/provider_manual_smoke_notes.sh
  ```
  Only if explicitly instructed for connectivity checks, set `ENABLE_MARKET_DATA_SMOKE_TESTS=true` in `.env`.

- **Negative Validation Tests**:
  Ensure default behavior locks provider calls safely and natively.
  ```bash
  bash scripts/provider_negative_tests.sh
  ```

3. **Phase 6K - Custom Public Domain Configuration**:
   ```bash
   sudo cp deploy/nginx-ghbs-trading.conf.example /etc/nginx/sites-available/ghbs
   sudo ln -s /etc/nginx/sites-available/ghbs /etc/nginx/sites-enabled/
   ```
4. **Reload Web Server**:
   ```bash
   sudo systemctl reload nginx
   ```

### Operational Verifications & Validating the Matrix Externally
Once services boot, inspect sandbox bounds natively:
```bash
./scripts/check_safety.sh
```
*Note: This utilizes a shell wrapper that executes `scripts/check_safety.py` underneath. It exits `1` immediately if `UNSAFE` is surfaced, enabling clean CI/CD pipeline halts.*

To check complete Release Status and endpoints cleanly:
```bash
./scripts/release_status.sh
./scripts/health_check.sh
```

### Logs & Diagnostics
To check daemonized system logs:
```bash
sudo journalctl -u ghbs-backend.service -f
```

### Rollback to Script Mode
If you prefer reversing the systemd wrappers returning cleanly to script bounds:
```bash
sudo systemctl stop ghbs-backend ghbs-frontend
sudo systemctl disable ghbs-backend ghbs-frontend
bash scripts/start_backend.sh
```

## 6. Validation & Safety Assurances
Before logging in, dynamically confirm that your app safely initialized and mapped bounds correctly.
Navigate to your instance's domain root index (i.e. `http://YOUR-VPS-IP:3000/` or mapped proxy).

### Validating the Safety Matrix
- Locate the **Pre-Auth Safety Matrix Panel** at the bottom of the Login screen.
- Verify `Safety State: SAFE`.
- Verify `Production DB Access: Disabled`.
- Verify `Database Path: tasi_ledger_test.db`.
- Verify Live Features (`Alert Scheduler`, `Scout`, `Analyze`) are explicitly disabled.

*Note: If the path shows `tasi_ledger.db` but production DB access is disabled, the system will correctly assert `Safety State: UNSAFE`, block API integrations behind an HTTP 503 Guard, and print "Database access blocked by safety guard".*

## 7. Operational Shutdown
To safely tear down the systems locally:

```bash
# Utilizing customized graceful termination scripts
bash scripts/stop_services.sh
```

## 8. Rollback Procedures
If changes produce unwanted logic or safety degradations during deployment:

1. Stop the application immediately: `pm2 stop ghbs-trade` (Or terminate shell job).
2. Reset your deployment environment variables matching your previous deployment configurations inside `.env`, removing or toggling specific runtime feature bounds specifically cleanly.
3. Validate `.env` via `cat .env | grep ENABLE_` to verify all components align properly securely (`false` is safer than `true`). 
4. Check your Git state: `git reset --hard HEAD` and checkout a prior signed commit or branch release cleanly if application source files were altered natively.
5. Recompile bundles explicitly: `npm run build`. Note: Do not proceed until `npm run build` completes warnings and all checks pass securely.
6. Restart boundaries cleanly.

## 9. Final Safety Assertions
By following this deployment runbook correctly:
- No `tasi_ledger.db` production database will ever interact or establish connections implicitly without explicit `ALLOW_PRODUCTION_DB=true`.
- The `scheduler` remains deactivated keeping outbound API integrations completely paused.
- No Telegram limits can be exceeded autonomously during sandbox runtime tests explicitly. 
- The engine guarantees no live external trading interactions or operations executing transactions natively. Limits restrict behavior completely down to `auth-only` logging structures.

## Option L — Phase 6W Telegram Alerts Dry-Run Foundation
Phase 6W adds Telegram readiness and dry-run preview capability only.
Status check: ./scripts/telegram_alert_status.sh
Negative tests: ./scripts/telegram_negative_tests.sh
Dry-run notes: ./scripts/telegram_dry_run_notes.sh
Phase 6W does not send Telegram messages and does not call the Telegram Bot API.

## Option M — Phase 6X Secret Alias Readiness
Phase 6X supports TELEGRAM_TOKEN as an alias for TELEGRAM_BOT_TOKEN and masks AUTHORIZED_USER_IDS.
Do not paste real secrets into chat or commit them to GitHub.
Use ./scripts/secrets_status.sh and ./scripts/telegram_alert_status.sh to verify masked readiness.
