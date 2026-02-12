"""FastAPI application exposing users, watchlists, and manual checks."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    clear_otp_failures,
    consume_valid_code,
    create_auth_code,
    create_session,
    ensure_otp_not_blocked,
    get_current_user,
    record_otp_failure,
    revoke_session,
    send_email_otp,
    send_sms_otp,
)
from .database import create_all_tables
from .deps import get_db
from .orm_models import PriceCheckRun, User, WatchlistItem, utc_now
from .schemas import (
    AuthCodeVerify,
    AuthFlowResponse,
    AuthLoginStart,
    AuthRegisterStart,
    AuthTokenResponse,
    PriceCheckRunRead,
    UserCreate,
    UserRead,
    WatchlistItemCreate,
    WatchlistItemRead,
    WatchlistItemUpdate,
)
from .scrape_runner import run_check_for_item
from .settings import load_settings

app = FastAPI(title="Plugin Boutique Price Checker API", version="0.1.0")
DBDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]
STATIC_DIR = Path(__file__).parent / "static"
settings = load_settings()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure DB schema exists before serving requests."""
    if settings.db_auto_create:
        create_all_tables()


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness endpoint."""
    return {"status": "ok"}


@app.get("/ready")
def ready(db: DBDep) -> dict[str, str]:
    """Readiness endpoint with DB connectivity check."""
    db.execute(select(1))
    return {"status": "ready"}


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the minimal frontend dashboard."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Return an empty favicon response to avoid noisy 404 logs."""
    return Response(status_code=204)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_ttl_hours * 3600,
    )


@app.post("/auth/register/start", response_model=AuthFlowResponse)
def auth_register_start(payload: AuthRegisterStart, db: DBDep) -> AuthFlowResponse:
    """Create pending user and send email verification code."""
    settings = load_settings()
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        user = User(email=payload.email, phone_number=payload.phone_number)
    else:
        if user.email_verified_at and user.phone_verified_at and user.two_factor_enabled:
            raise HTTPException(status_code=409, detail="User is already fully registered")
        user.phone_number = payload.phone_number

    db.add(user)
    db.commit()
    db.refresh(user)

    _code_row, plain_code = create_auth_code(db, user, purpose="email_verify", channel="email")
    if settings.auth_dev_mode:
        return AuthFlowResponse(message="Email verification code generated (dev mode).", dev_code=plain_code)

    send_email_otp(str(payload.email), plain_code)
    return AuthFlowResponse(message="Email verification code sent.")


@app.post("/auth/register/verify-email", response_model=AuthFlowResponse)
def auth_register_verify_email(payload: AuthCodeVerify, request: Request, db: DBDep) -> AuthFlowResponse:
    """Validate email OTP, mark email verified, and send phone OTP."""
    settings = load_settings()
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.phone_number:
        raise HTTPException(status_code=400, detail="Phone number missing on user")

    source_ip = request.client.host if request.client else "unknown"
    ensure_otp_not_blocked(db, email=str(payload.email), purpose="email_verify", source_ip=source_ip)
    try:
        consume_valid_code(db, user=user, purpose="email_verify", plain_code=payload.code)
    except HTTPException as exc:
        if exc.status_code == 400:
            record_otp_failure(db, email=str(payload.email), purpose="email_verify", source_ip=source_ip)
            ensure_otp_not_blocked(db, email=str(payload.email), purpose="email_verify", source_ip=source_ip)
        raise

    clear_otp_failures(db, email=str(payload.email), purpose="email_verify", source_ip=source_ip)
    user.email_verified_at = user.email_verified_at or utc_now()
    db.add(user)
    db.commit()
    db.refresh(user)

    _code_row, plain_code = create_auth_code(db, user, purpose="phone_verify", channel="sms")
    if settings.auth_dev_mode:
        return AuthFlowResponse(message="Phone verification code generated (dev mode).", dev_code=plain_code)

    send_sms_otp(user.phone_number, plain_code)
    return AuthFlowResponse(message="Phone verification code sent.")


@app.post("/auth/register/verify-phone", response_model=AuthTokenResponse)
def auth_register_verify_phone(payload: AuthCodeVerify, request: Request, response: Response, db: DBDep) -> AuthTokenResponse:
    """Validate phone OTP and create bearer session."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    source_ip = request.client.host if request.client else "unknown"
    ensure_otp_not_blocked(db, email=str(payload.email), purpose="phone_verify", source_ip=source_ip)
    try:
        consume_valid_code(db, user=user, purpose="phone_verify", plain_code=payload.code)
    except HTTPException as exc:
        if exc.status_code == 400:
            record_otp_failure(db, email=str(payload.email), purpose="phone_verify", source_ip=source_ip)
            ensure_otp_not_blocked(db, email=str(payload.email), purpose="phone_verify", source_ip=source_ip)
        raise

    clear_otp_failures(db, email=str(payload.email), purpose="phone_verify", source_ip=source_ip)
    user.phone_verified_at = user.phone_verified_at or utc_now()
    user.two_factor_enabled = True
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(db, user)
    _set_auth_cookie(response, token)
    return AuthTokenResponse(access_token=token, user=user)


@app.post("/auth/login/start", response_model=AuthFlowResponse)
def auth_login_start(payload: AuthLoginStart, db: DBDep) -> AuthFlowResponse:
    """Start login 2FA for an existing verified user."""
    settings = load_settings()
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.email_verified_at or not user.two_factor_enabled or not user.phone_number:
        raise HTTPException(status_code=400, detail="User is not fully verified for 2FA login")

    _code_row, plain_code = create_auth_code(db, user, purpose="login_2fa", channel="sms")
    if settings.auth_dev_mode:
        return AuthFlowResponse(message="Login 2FA code generated (dev mode).", dev_code=plain_code)

    send_sms_otp(user.phone_number, plain_code)
    return AuthFlowResponse(message="Login 2FA code sent.")


@app.post("/auth/login/verify", response_model=AuthTokenResponse)
def auth_login_verify(payload: AuthCodeVerify, request: Request, response: Response, db: DBDep) -> AuthTokenResponse:
    """Verify login 2FA code and return bearer token."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    source_ip = request.client.host if request.client else "unknown"
    ensure_otp_not_blocked(db, email=str(payload.email), purpose="login_2fa", source_ip=source_ip)
    try:
        consume_valid_code(db, user=user, purpose="login_2fa", plain_code=payload.code)
    except HTTPException as exc:
        if exc.status_code == 400:
            record_otp_failure(db, email=str(payload.email), purpose="login_2fa", source_ip=source_ip)
            ensure_otp_not_blocked(db, email=str(payload.email), purpose="login_2fa", source_ip=source_ip)
        raise

    clear_otp_failures(db, email=str(payload.email), purpose="login_2fa", source_ip=source_ip)
    token = create_session(db, user)
    _set_auth_cookie(response, token)
    return AuthTokenResponse(access_token=token, user=user)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def auth_logout(request: Request, response: Response, db: DBDep) -> Response:
    """Revoke current session token and clear auth cookie."""
    token: str | None = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get(settings.auth_cookie_name)

    if token:
        revoke_session(db, token)

    response.delete_cookie(settings.auth_cookie_name)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@app.get("/me", response_model=UserRead)
def get_me(current_user: UserDep) -> User:
    """Return authenticated user profile."""
    return current_user


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DBDep) -> User:
    """Create one user by email."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/me/watchlist-items", response_model=WatchlistItemRead, status_code=status.HTTP_201_CREATED)
def create_my_watchlist_item(payload: WatchlistItemCreate, db: DBDep, current_user: UserDep) -> WatchlistItem:
    """Create watchlist item for current authenticated user."""
    item = WatchlistItem(
        user_id=current_user.id,
        product_url=payload.product_url,
        threshold=payload.threshold,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/me/watchlist-items", response_model=list[WatchlistItemRead])
def list_my_watchlist_items(db: DBDep, current_user: UserDep) -> list[WatchlistItem]:
    """List watchlist items for current authenticated user."""
    stmt = select(WatchlistItem).where(WatchlistItem.user_id == current_user.id).order_by(WatchlistItem.id)
    return list(db.scalars(stmt).all())


@app.patch("/me/watchlist-items/{item_id}", response_model=WatchlistItemRead)
def update_my_watchlist_item(item_id: int, payload: WatchlistItemUpdate, db: DBDep, current_user: UserDep) -> WatchlistItem:
    """Update own watchlist item."""
    item = db.get(WatchlistItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if payload.threshold is not None:
        item.threshold = payload.threshold
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/me/watchlist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_watchlist_item(item_id: int, db: DBDep, current_user: UserDep) -> Response:
    """Delete own watchlist item and related run history."""
    item = db.get(WatchlistItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    db.execute(delete(PriceCheckRun).where(PriceCheckRun.watchlist_item_id == item_id))
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/me/watchlist-items/{item_id}/check", response_model=PriceCheckRunRead)
def check_my_watchlist_item(item_id: int, db: DBDep, current_user: UserDep) -> PriceCheckRun:
    """Run check for own active watchlist item."""
    item = db.get(WatchlistItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    if not item.is_active:
        raise HTTPException(status_code=400, detail="Watchlist item is inactive")

    return run_check_for_item(db, item)


@app.get("/me/watchlist-items/{item_id}/runs", response_model=list[PriceCheckRunRead])
def list_my_runs(item_id: int, db: DBDep, current_user: UserDep) -> list[PriceCheckRun]:
    """List check history for own watchlist item."""
    item = db.get(WatchlistItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    stmt = select(PriceCheckRun).where(PriceCheckRun.watchlist_item_id == item_id).order_by(PriceCheckRun.id.desc())
    return list(db.scalars(stmt).all())


@app.get("/users", response_model=list[UserRead])
def list_users(db: DBDep) -> list[User]:
    """List all users."""
    return list(db.scalars(select(User).order_by(User.id)).all())


@app.post(
    "/users/{user_id}/watchlist-items",
    response_model=WatchlistItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_watchlist_item(user_id: int, payload: WatchlistItemCreate, db: DBDep) -> WatchlistItem:
    """Add one watchlist item for a specific user."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item = WatchlistItem(
        user_id=user_id,
        product_url=payload.product_url,
        threshold=payload.threshold,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/users/{user_id}/watchlist-items", response_model=list[WatchlistItemRead])
def list_watchlist_items(user_id: int, db: DBDep) -> list[WatchlistItem]:
    """List one user's watchlist items."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(WatchlistItem).where(WatchlistItem.user_id == user_id).order_by(WatchlistItem.id)
    return list(db.scalars(stmt).all())


@app.patch("/watchlist-items/{item_id}", response_model=WatchlistItemRead)
def update_watchlist_item(item_id: int, payload: WatchlistItemUpdate, db: DBDep) -> WatchlistItem:
    """Update threshold and/or active flag for one item."""
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if payload.threshold is not None:
        item.threshold = payload.threshold
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/watchlist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(item_id: int, db: DBDep) -> Response:
    """Delete one watchlist item and its run history."""
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    db.execute(delete(PriceCheckRun).where(PriceCheckRun.watchlist_item_id == item_id))
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/watchlist-items/{item_id}/check", response_model=PriceCheckRunRead)
def check_watchlist_item(item_id: int, db: DBDep) -> PriceCheckRun:
    """Run a check immediately for one watchlist item."""
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    if not item.is_active:
        raise HTTPException(status_code=400, detail="Watchlist item is inactive")

    return run_check_for_item(db, item)


@app.get("/watchlist-items/{item_id}/runs", response_model=list[PriceCheckRunRead])
def list_runs(item_id: int, db: DBDep) -> list[PriceCheckRun]:
    """Show historical check runs for an item."""
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    stmt = select(PriceCheckRun).where(PriceCheckRun.watchlist_item_id == item_id).order_by(PriceCheckRun.id.desc())
    return list(db.scalars(stmt).all())
