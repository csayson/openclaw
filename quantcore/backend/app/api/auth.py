from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
import structlog

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_totp_secret,
    get_totp_uri, verify_totp,
)
from app.models.account import User

log = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    country: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    totp_required: bool = False


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        country=body.country,
    )
    db.add(user)
    await db.commit()
    # TODO: send verification email via SendGrid
    return {"message": "Registration successful. Check your email to verify."}


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user: User | None = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Lockout check
    if user.lockout_until and user.lockout_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Account locked. Try later.")

    if not verify_password(form.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.failed_login_attempts = 0
    user.lockout_until = None
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        totp_required=user.totp_enabled,
    )


@router.post("/totp/verify")
async def verify_totp_code(code: str, current_user: User = Depends(get_current_user)):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not configured")
    if not verify_totp(current_user.totp_secret, code):
        raise HTTPException(status_code=401, detail="Invalid TOTP code")
    return {"verified": True}


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    current_user.totp_secret = secret
    await db.commit()
    return TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/enable")
async def enable_totp(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret or not verify_totp(current_user.totp_secret, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.totp_enabled = True
    await db.commit()
    return {"message": "2FA enabled"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
