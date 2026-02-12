"""Pydantic schemas used by the API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for creating a user."""

    email: EmailStr


class UserRead(BaseModel):
    """API response for user rows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    phone_number: str | None
    email_verified_at: datetime | None
    phone_verified_at: datetime | None
    two_factor_enabled: bool
    created_at: datetime


class WatchlistItemCreate(BaseModel):
    """Request body for creating watchlist items."""

    product_url: str = Field(min_length=1)
    threshold: float = Field(gt=0)
    is_active: bool = True


class WatchlistItemUpdate(BaseModel):
    """Request body for updating watchlist items."""

    threshold: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class WatchlistItemRead(BaseModel):
    """API response for watchlist rows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_url: str
    threshold: float
    is_active: bool
    last_price: float | None
    last_currency: str | None
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PriceCheckRunRead(BaseModel):
    """API response for worker run audit rows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_item_id: int
    status: str
    message: str
    price_amount: float | None
    price_currency: str | None
    alert_sent: bool
    created_at: datetime


class AuthRegisterStart(BaseModel):
    """Start registration with email and phone."""

    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=32)


class AuthCodeVerify(BaseModel):
    """Verify an OTP for a specific email."""

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class AuthLoginStart(BaseModel):
    """Start login 2FA for an existing user."""

    email: EmailStr


class AuthFlowResponse(BaseModel):
    """Generic auth step response with optional dev OTP visibility."""

    message: str
    dev_code: str | None = None


class AuthTokenResponse(BaseModel):
    """Bearer token response returned after successful auth."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead
