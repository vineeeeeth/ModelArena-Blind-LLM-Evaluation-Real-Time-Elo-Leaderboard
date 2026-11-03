"""Authentication API router – JWT, Argon2id, cookie-based session, email verification, password reset."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.logging import logger
from app.core.redis import redis
from app.core.security import (
    check_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.tables import (
    AnonSession,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
    UserRole,
)
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(tags=["auth"])
settings = get_settings()

MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 900  # 15 minutes


async def check_login_rate_limit(ip: str, email: str) -> None:
    ip_key = f"login_fail:ip:{ip}"
    email_key = f"login_fail:email:{email}"
    ip_fails = int(await redis.get(ip_key) or 0)
    email_fails = int(await redis.get(email_key) or 0)

    if ip_fails >= MAX_FAILED_LOGINS or email_fails >= MAX_FAILED_LOGINS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again after 15 minutes.",
        )


async def record_failed_login(ip: str, email: str) -> None:
    ip_key = f"login_fail:ip:{ip}"
    email_key = f"login_fail:email:{email}"
    await redis.incr(ip_key)
    await redis.expire(ip_key, LOCKOUT_SECONDS)
    await redis.incr(email_key)
    await redis.expire(email_key, LOCKOUT_SECONDS)


async def clear_failed_login(ip: str, email: str) -> None:
    await redis.delete(f"login_fail:ip:{ip}")
    await redis.delete(f"login_fail:email:{email}")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> User:
    token = access_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user_uuid = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    try:
        return await get_current_user(request, db, access_token, authorization)
    except HTTPException:
        return None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Can be True in HTTPS
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/",
    )


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # 1. Validate password strength
    pwd_err = check_password_strength(data.password)
    if pwd_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_err)

    # 2. Check if email already registered
    existing = (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    # 3. Create user
    pwd_hash = hash_password(data.password)
    user = User(
        email=data.email.lower(),
        password_hash=pwd_hash,
        display_name=data.display_name,
        is_email_verified=False,
        role=UserRole.user,
    )
    db.add(user)
    await db.flush()

    # Link anonymous session if present
    anon_id_cookie = request.cookies.get("arena_session")
    if anon_id_cookie:
        try:
            anon_uuid = uuid.UUID(anon_id_cookie)
            anon_res = await db.execute(select(AnonSession).where(AnonSession.id == anon_uuid))
            anon_sess = anon_res.scalar_one_or_none()
            if anon_sess:
                anon_sess.user_id = user.id
        except Exception:
            pass

    # 4. Generate verification token & send email
    raw_tok, hashed_tok = generate_token()
    verif = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashed_tok,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verif)

    # 5. Issue JWT and Refresh token
    access_tok = create_access_token(str(user.id), {"role": user.role.value})
    raw_refresh, hashed_refresh, refresh_exp = create_refresh_token(str(user.id))
    rt_entry = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=refresh_exp,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(rt_entry)
    await db.commit()

    # Send verification email asynchronously
    try:
        await send_verification_email(user.email, raw_tok, settings.frontend_url)
    except Exception as exc:
        logger.warning("failed_to_send_verification_email", error=str(exc))

    set_auth_cookies(response, access_tok, raw_refresh)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    ip = request.client.host if request.client else "unknown"
    await check_login_rate_limit(ip, data.email.lower())

    res = await db.execute(select(User).where(User.email == data.email.lower()))
    user = res.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        await record_failed_login(ip, data.email.lower())
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    await clear_failed_login(ip, data.email.lower())

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Link anonymous session if present
    anon_id_cookie = request.cookies.get("arena_session")
    if anon_id_cookie:
        try:
            anon_uuid = uuid.UUID(anon_id_cookie)
            anon_res = await db.execute(select(AnonSession).where(AnonSession.id == anon_uuid))
            anon_sess = anon_res.scalar_one_or_none()
            if anon_sess:
                anon_sess.user_id = user.id
        except Exception:
            pass

    access_tok = create_access_token(str(user.id), {"role": user.role.value})
    raw_refresh, hashed_refresh, refresh_exp = create_refresh_token(str(user.id))
    rt_entry = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=refresh_exp,
        user_agent=request.headers.get("user-agent"),
        ip=ip,
    )
    db.add(rt_entry)
    await db.commit()

    set_auth_cookies(response, access_tok, raw_refresh)
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None),
) -> dict[str, str]:
    if refresh_token:
        h = hash_token(refresh_token)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == h, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens_endpoint(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing.")

    h = hash_token(refresh_token)
    now = datetime.now(timezone.utc)
    res = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == h,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    rt = res.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    # Revoke old refresh token
    rt.revoked_at = now

    # Get user
    user_res = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    # Issue new access + rotated refresh token
    new_access = create_access_token(str(user.id), {"role": user.role.value})
    new_raw_refresh, new_hashed_refresh, refresh_exp = create_refresh_token(str(user.id))
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hashed_refresh,
        expires_at=refresh_exp,
    )
    db.add(new_rt)
    await db.commit()

    set_auth_cookies(response, new_access, new_raw_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    h = hash_token(token)
    now = datetime.now(timezone.utc)
    res = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == h,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
    )
    tok_obj = res.scalar_one_or_none()
    if not tok_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

    tok_obj.used_at = now
    await db.execute(
        update(User).where(User.id == tok_obj.user_id).values(is_email_verified=True)
    )
    await db.commit()
    return {"message": "Email verified successfully."}


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if current_user.is_email_verified:
        return {"message": "Email is already verified."}

    raw_tok, hashed_tok = generate_token()
    verif = EmailVerificationToken(
        user_id=current_user.id,
        token_hash=hashed_tok,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verif)
    await db.commit()

    await send_verification_email(current_user.email, raw_tok, settings.frontend_url)
    return {"message": "Verification email sent."}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    res = await db.execute(select(User).where(User.email == data.email.lower()))
    user = res.scalar_one_or_none()
    if user:
        raw_tok, hashed_tok = generate_token()
        reset_tok = PasswordResetToken(
            user_id=user.id,
            token_hash=hashed_tok,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_tok)
        await db.commit()
        await send_password_reset_email(user.email, raw_tok, settings.frontend_url)

    # Always return 200 to prevent user enumeration
    return {"message": "If this email is registered, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    pwd_err = check_password_strength(data.new_password)
    if pwd_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_err)

    h = hash_token(data.token)
    now = datetime.now(timezone.utc)
    res = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == h,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    tok_obj = res.scalar_one_or_none()
    if not tok_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    tok_obj.used_at = now
    new_hash = hash_password(data.new_password)
    await db.execute(update(User).where(User.id == tok_obj.user_id).values(password_hash=new_hash))
    await db.commit()
    return {"message": "Password reset successfully. You can now log in."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)

