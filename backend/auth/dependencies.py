from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import aiosqlite
from pydantic import BaseModel, ValidationError

from backend.db.database import get_db
from backend.auth.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class TokenPayload(BaseModel):
    sub: str = None

async def get_current_user(
    db: aiosqlite.Connection = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    async with db.execute("SELECT id, username, role FROM users WHERE id = ?", (token_data.sub,)) as cursor:
        user = await cursor.fetchone()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return dict(user)
