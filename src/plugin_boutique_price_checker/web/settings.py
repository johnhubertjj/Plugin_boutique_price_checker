"""Runtime settings for the API/worker scaffold."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Environment-backed settings used by web and worker processes."""

    database_url: str
    smtp_address: str | None
    email_address: str | None
    email_password: str | None
    worker_sleep_seconds: int
    auth_dev_mode: bool
    auth_code_ttl_minutes: int
    auth_session_ttl_hours: int
    auth_otp_max_attempts: int
    auth_otp_window_minutes: int
    auth_otp_block_minutes: int
    twilio_account_sid: str | None
    twilio_auth_token: str | None
    twilio_from_number: str | None
    twilio_messaging_service_sid: str | None
    environment: str
    cors_allowed_origins_raw: str
    auth_cookie_name: str
    auth_cookie_secure: bool
    db_auto_create: bool

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""
        if not self.cors_allowed_origins_raw.strip():
            return []
        return [origin.strip() for origin in self.cors_allowed_origins_raw.split(",") if origin.strip()]


def load_settings() -> Settings:
    """Read settings from environment variables with safe defaults."""
    auth_dev_mode_raw = os.getenv("AUTH_DEV_MODE", "true").strip().lower()
    auth_cookie_secure_raw = os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower()
    db_auto_create_raw = os.getenv("DB_AUTO_CREATE", "true").strip().lower()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./plugin_boutique.db"),
        smtp_address=os.getenv("SMTP_ADDRESS"),
        email_address=os.getenv("EMAIL_ADDRESS"),
        email_password=os.getenv("EMAIL_PASSWORD"),
        worker_sleep_seconds=int(os.getenv("WORKER_SLEEP_SECONDS", "300")),
        auth_dev_mode=auth_dev_mode_raw in {"1", "true", "yes", "on"},
        auth_code_ttl_minutes=int(os.getenv("AUTH_CODE_TTL_MINUTES", "10")),
        auth_session_ttl_hours=int(os.getenv("AUTH_SESSION_TTL_HOURS", "168")),
        auth_otp_max_attempts=int(os.getenv("AUTH_OTP_MAX_ATTEMPTS", "5")),
        auth_otp_window_minutes=int(os.getenv("AUTH_OTP_WINDOW_MINUTES", "15")),
        auth_otp_block_minutes=int(os.getenv("AUTH_OTP_BLOCK_MINUTES", "30")),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
        twilio_messaging_service_sid=os.getenv("TWILIO_MESSAGING_SERVICE_SID"),
        environment=os.getenv("APP_ENV", "development"),
        cors_allowed_origins_raw=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"),
        auth_cookie_name=os.getenv("AUTH_COOKIE_NAME", "pb_session"),
        auth_cookie_secure=auth_cookie_secure_raw in {"1", "true", "yes", "on"},
        db_auto_create=db_auto_create_raw in {"1", "true", "yes", "on"},
    )
