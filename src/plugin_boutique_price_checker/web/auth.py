"""Authentication helpers for email verification and phone 2FA."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import smtplib
from email.message import EmailMessage

from fastapi import Depends, Header, HTTPException, Request
import httpx
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .deps import get_db
from .orm_models import AuthCode, AuthSession, OtpAttempt, User, utc_now
from .settings import load_settings


def hash_secret(value: str) -> str:
    """Return stable SHA-256 digest for stored tokens/codes."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_code() -> str:
    """Generate a six-digit numeric OTP code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def create_auth_code(db: Session, user: User, purpose: str, channel: str) -> tuple[AuthCode, str]:
    """Create a new OTP row and return the plain code for delivery."""
    settings = load_settings()
    plain_code = generate_code()
    code = AuthCode(
        user_id=user.id,
        purpose=purpose,
        channel=channel,
        code_hash=hash_secret(plain_code),
        expires_at=utc_now() + timedelta(minutes=settings.auth_code_ttl_minutes),
    )
    db.add(code)
    db.commit()
    db.refresh(code)
    return code, plain_code


def consume_valid_code(db: Session, user: User, purpose: str, plain_code: str) -> AuthCode:
    """Validate and consume the latest unconsumed code for purpose."""
    now = utc_now()
    stmt = (
        select(AuthCode)
        .where(
            and_(
                AuthCode.user_id == user.id,
                AuthCode.purpose == purpose,
                AuthCode.consumed_at.is_(None),
                AuthCode.expires_at >= now,
            )
        )
        .order_by(AuthCode.id.desc())
    )
    candidate = db.scalar(stmt)
    if candidate is None or candidate.code_hash != hash_secret(plain_code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    candidate.consumed_at = now
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def create_session(db: Session, user: User) -> str:
    """Create and persist a bearer session token."""
    settings = load_settings()
    plain_token = secrets.token_urlsafe(32)
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_secret(plain_token),
        expires_at=utc_now() + timedelta(hours=settings.auth_session_ttl_hours),
    )
    db.add(session)
    db.commit()
    return plain_token


def revoke_session(db: Session, token: str) -> None:
    """Revoke an auth session token if it exists."""
    token_hash = hash_secret(token)
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
    if session is None:
        return
    session.revoked_at = utc_now()
    db.add(session)
    db.commit()


def _otp_attempt_key(email: str, purpose: str, source_ip: str) -> str:
    return f"{email.strip().lower()}::{purpose.strip().lower()}::{source_ip.strip().lower()}"


def _as_aware_utc(value: datetime) -> datetime:
    """Normalize DB datetimes to aware UTC for safe comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def ensure_otp_not_blocked(db: Session, email: str, purpose: str, source_ip: str) -> None:
    """Raise 429 when OTP verification is currently blocked."""
    key = _otp_attempt_key(email=email, purpose=purpose, source_ip=source_ip)
    attempt = db.scalar(select(OtpAttempt).where(OtpAttempt.subject_key == key))
    if attempt and attempt.blocked_until and _as_aware_utc(attempt.blocked_until) > utc_now():
        raise HTTPException(status_code=429, detail="Too many invalid code attempts. Try again later.")


def record_otp_failure(db: Session, email: str, purpose: str, source_ip: str) -> None:
    """Increment failure count and block when configured threshold is reached."""
    settings = load_settings()
    now = utc_now()
    key = _otp_attempt_key(email=email, purpose=purpose, source_ip=source_ip)
    attempt = db.scalar(select(OtpAttempt).where(OtpAttempt.subject_key == key))
    if attempt is None:
        attempt = OtpAttempt(subject_key=key, fail_count=1, window_started_at=now, blocked_until=None)
    else:
        window_limit = attempt.window_started_at + timedelta(minutes=settings.auth_otp_window_minutes)
        window_limit = _as_aware_utc(window_limit)
        if now > window_limit:
            attempt.fail_count = 1
            attempt.window_started_at = now
            attempt.blocked_until = None
        else:
            attempt.fail_count += 1

        if attempt.fail_count >= settings.auth_otp_max_attempts:
            attempt.blocked_until = now + timedelta(minutes=settings.auth_otp_block_minutes)

    db.add(attempt)
    db.commit()


def clear_otp_failures(db: Session, email: str, purpose: str, source_ip: str) -> None:
    """Clear failure counters after successful verification."""
    key = _otp_attempt_key(email=email, purpose=purpose, source_ip=source_ip)
    attempt = db.scalar(select(OtpAttempt).where(OtpAttempt.subject_key == key))
    if attempt is None:
        return
    db.delete(attempt)
    db.commit()


def send_email_otp(to_email: str, code: str) -> None:
    """Send verification OTP via SMTP."""
    settings = load_settings()
    if not settings.smtp_address or not settings.email_address or not settings.email_password:
        raise HTTPException(status_code=500, detail="SMTP settings are missing for email OTP delivery")

    msg = EmailMessage()
    msg["Subject"] = "Your Plugin Boutique verification code"
    msg["From"] = settings.email_address
    msg["To"] = to_email
    msg.set_content(f"Your verification code is: {code}\nThis code expires shortly.")

    with smtplib.SMTP_SSL(settings.smtp_address, 465) as smtp:
        smtp.login(settings.email_address, settings.email_password)
        smtp.send_message(msg)


def send_sms_otp(phone_number: str, code: str) -> None:
    """Send SMS OTP via Twilio REST API."""
    settings = load_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise HTTPException(status_code=500, detail="Twilio credentials are missing for SMS OTP delivery")
    if not settings.twilio_from_number and not settings.twilio_messaging_service_sid:
        raise HTTPException(
            status_code=500,
            detail="Set TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID for SMS OTP delivery",
        )

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    data = {
        "To": phone_number,
        "Body": f"Your Plugin Boutique verification code is {code}.",
    }
    if settings.twilio_messaging_service_sid:
        data["MessagingServiceSid"] = settings.twilio_messaging_service_sid
    else:
        data["From"] = settings.twilio_from_number

    try:
        response = httpx.post(
            url,
            data=data,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach Twilio: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Twilio SMS send failed ({response.status_code})")


def get_current_user(
    authorization: str | None = Header(default=None),
    request: Request = None,
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from Bearer token."""
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif request is not None:
        settings = load_settings()
        token = request.cookies.get(settings.auth_cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token_hash = hash_secret(token)
    now = utc_now()

    stmt = select(AuthSession).where(
        and_(
            AuthSession.token_hash == token_hash,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at >= now,
        )
    )
    session = db.scalar(stmt)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User for token not found")
    return user
