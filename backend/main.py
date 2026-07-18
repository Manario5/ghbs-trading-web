from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
import aiosqlite

from backend.api.router import api_router
from backend.db.database import init_db, get_db_path
from backend.auth.security import get_password_hash

import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def seed_sandbox_user():
    allow_prod = os.environ.get("ALLOW_PRODUCTION_DB", "false").lower() == "true"
    try:
        db_path = get_db_path()
        if not allow_prod and "tasi_ledger.db" not in db_path:
            async with aiosqlite.connect(db_path) as db:
                async with db.execute("SELECT id FROM users WHERE username = ?", ("sandbox_admin",)) as cursor:
                    user = await cursor.fetchone()
                
                if not user:
                    now = datetime.utcnow().isoformat()
                    hashed_pw = get_password_hash("SandboxTest123!")
                    await db.execute(
                        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                        ("sandbox_admin", hashed_pw, "admin", now)
                    )
                    await db.commit()
                    print("Sandbox seed user 'sandbox_admin' created successfully.")
    except HTTPException:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        await seed_sandbox_user()
    except HTTPException as e:
        print(f"Startup warning: {e.detail}. Running in degraded state.")
    except Exception as e:
        print(f"Startup error: {str(e)}")
    yield

app = FastAPI(title="GHBS Trading - Command Center", version="1.0.0-alpha", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
