import aiosqlite
import os

def is_db_blocked() -> bool:
    path = os.environ.get("DB_PATH", "tasi_ledger_test.db")
    if "tasi_ledger.db" in path:
        allow_prod = os.environ.get("ALLOW_PRODUCTION_DB", "false").lower() == "true"
        if not allow_prod:
            return True
    return False

def assert_db_allowed():
    if is_db_blocked():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database access blocked by safety guard.")

def get_db_path() -> str:
    return os.environ.get("DB_PATH", "tasi_ledger_test.db")



async def get_db():
    assert_db_allowed()
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    if is_db_blocked():
        print("Startup warning: DB_PATH points to production but ALLOW_PRODUCTION_DB=false. Running in degraded state.")
        return
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")

        # 1. Existing Engine Tables (preserve exactly)
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker                    TEXT    NOT NULL,
                position_state            TEXT    NOT NULL,
                opened_at                 TEXT    NOT NULL,
                closed_at                 TEXT,
                initial_entry_price       REAL    NOT NULL,
                avg_cost                  REAL    NOT NULL,
                initial_atr               REAL    NOT NULL,
                original_position_size    INTEGER NOT NULL,
                current_position_size     INTEGER NOT NULL,
                highest_close_since_entry REAL    NOT NULL,
                stop_atr_multiple         REAL    NOT NULL,
                risk_per_trade_pct        REAL    NOT NULL,
                partial_exit_taken        INTEGER NOT NULL DEFAULT 0,
                last_stop_alert_date      TEXT,
                exit_reason               TEXT,
                realized_pnl_sar          REAL    NOT NULL DEFAULT 0,
                total_commissions_sar     REAL    NOT NULL DEFAULT 0,
                initial_risk_sar          REAL    DEFAULT 0,
                take_profit_price         REAL    DEFAULT 0,
                tp1_price                 REAL    DEFAULT 0,
                tp2_price                 REAL    DEFAULT 0,
                tp3_price                 REAL    DEFAULT 0,
                tp1_hit                   INTEGER DEFAULT 0,
                notes                     TEXT,
                version                   INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id      INTEGER NOT NULL,
                ticker           TEXT    NOT NULL,
                transaction_type TEXT    NOT NULL,
                signal_time      TEXT    NOT NULL,
                execution_time   TEXT    NOT NULL,
                fill_price       REAL    NOT NULL,
                quantity         INTEGER NOT NULL,
                commission_sar   REAL    NOT NULL DEFAULT 0,
                reason_code      TEXT    NOT NULL,
                equity_snapshot  REAL,
                realized_pnl_sar REAL    DEFAULT 0,
                r_multiple       REAL,
                duration_days    REAL,
                roi_pct          REAL,
                modeled_risk_sar REAL,
                realized_risk_sar REAL,
                slippage_sar      REAL,
                notes            TEXT,
                FOREIGN KEY (position_id) REFERENCES positions(id)
            );
            CREATE TABLE IF NOT EXISTS signal_events (
                signal_id    TEXT PRIMARY KEY,
                position_id  INTEGER,
                trade_date   TEXT NOT NULL,
                reason_code  TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                event_source TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS system_state (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS setup_log (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                logged_at              TEXT    NOT NULL,
                ticker                 TEXT    NOT NULL,
                setup_type             TEXT    NOT NULL,
                mechanical_actionable  INTEGER NOT NULL DEFAULT 1,
                mechanical_reason      TEXT,
                market_regime          TEXT,
                sector                 TEXT,
                sector_breadth         REAL,
                claude_signal          TEXT,
                confidence             INTEGER,
                adx                    REAL,
                rsi                    REAL,
                obv_trend              TEXT,
                vol_surge              REAL,
                entry_taken            INTEGER NOT NULL DEFAULT 0,
                position_id            INTEGER,
                outcome_r              REAL,
                tier                   TEXT,
                notes                  TEXT
            );
        """)

        # 2. Additive Web App Tables
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT,
                before_value TEXT,
                after_value TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS action_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                action_type TEXT NOT NULL,
                planned_price REAL,
                planned_quantity INTEGER,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                position_id INTEGER,
                transaction_id INTEGER,
                note_type TEXT NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                title TEXT,
                message TEXT NOT NULL,
                delivery_status TEXT NOT NULL,
                destination_masked TEXT,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS live_preview_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                preview_type TEXT NOT NULL,
                provider TEXT NOT NULL,
                ticker_count INTEGER NOT NULL,
                requested_ticker TEXT,
                scanned_count INTEGER NOT NULL,
                eligible_count INTEGER NOT NULL,
                blocked_count INTEGER NOT NULL,
                data_failures INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                notes TEXT
            );
        """)

        # Idempotent Migrations (if any needed down the road beyond original tables)
        
        await db.commit()
