from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
import sqlite3
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: sqlite3.Connection = Depends(get_db)):
    """
    Validate JWT token and return current user.
    Handles expired tokens, invalid tokens, and inactive users.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login?error=no_token"}
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": "/admin/login?error=invalid_token"}
            )
    except ExpiredSignatureError:
        # Token expired - clear cookie and redirect
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={
                "Location": "/admin/login?error=token_expired",
                "Set-Cookie": "access_token=; Max-Age=0; Path=/; HttpOnly"
            }
        )
    except JWTError as e:
        # Invalid token (malformed, wrong signature, etc.)
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={
                "Location": "/admin/login?error=invalid_token",
                "Set-Cookie": "access_token=; Max-Age=0; Path=/; HttpOnly"
            }
        )

    # Check if user exists and is active
    user = db.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1", 
        (user_id,)
    ).fetchone()
    
    if user is None:
        # User not found or inactive
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={
                "Location": "/admin/login?error=user_inactive",
                "Set-Cookie": "access_token=; Max-Age=0; Path=/; HttpOnly"
            }
        )
    
    return dict(user)


def require_role(*roles):
    """
    Dependency that requires user to have one of the specified roles.
    Usage: user = Depends(require_role("admin"))
           user = Depends(require_role("admin", "founder"))
    """
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required role: {', '.join(roles)}"
            )
        return user
    return role_checker
