from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import aiosqlite

from backend.db.database import get_db
from backend.auth.security import verify_password, create_access_token, get_password_hash
from backend.auth.dependencies import get_current_user
from backend.models.schemas import Token, User

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    db: aiosqlite.Connection = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    async with db.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)) as cursor:
        user = await cursor.fetchone()
        
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    return {
        "access_token": create_access_token(subject=user["id"]),
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
