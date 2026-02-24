# Deployable Scaffold Guide (API + Worker)

This guide explains what was added to make this project deployable as a backend for a web app or phone app.

It is intentionally practical:
- what was built
- why each piece exists
- how to run it
- what to build next for real production

## What was added

New package: `src/plugin_boutique_price_checker/web`

Files:
- `settings.py`: Reads runtime config from environment (`DATABASE_URL`, SMTP values, worker interval, auth settings).
- `database.py`: SQLAlchemy engine/session setup and table creation helper.
- `orm_models.py`: DB tables for `users`, `watchlist_items`, `price_check_runs`, `auth_codes`, and `auth_sessions`.
- `schemas.py`: FastAPI request/response schemas.
- `deps.py`: FastAPI DB session dependency.
- `scrape_runner.py`: Shared check logic used by API and worker.
- `api.py`: FastAPI routes for CRUD + manual check trigger.
- `static/index.html`, `static/styles.css`, `static/app.js`: minimal browser dashboard.
- `worker.py`: Polling background process for active watchlist checks.
- `server.py`: CLI entrypoint for starting the API with uvicorn.

Also updated:
- `pyproject.toml` dependencies and scripts
- `README.md` with quick start for deployable mode

## Why this architecture

Your existing CLI + Selenium scraper is useful, but not directly deployable as a user-facing app.

To support web/mobile clients, you need:
1. persistent data storage
2. an HTTP API
3. background execution for scraping
4. historical records of runs/errors

This scaffold splits those concerns:
- API handles user actions.
- Worker handles scraping cycles.
- Shared runner keeps scraping business logic in one place.

## Database migrations (Alembic)

Production should use Alembic migrations and set `DB_AUTO_CREATE=false`.

Local commands:

```bash
uv run alembic upgrade head
```

Create a new migration revision:

```bash
uv run alembic revision -m "describe change"
```

## Data model decisions

### `users`
- User identity + verification state.
- Fields include `email`, `phone_number`, `email_verified_at`, `phone_verified_at`, `two_factor_enabled`.

### `watchlist_items`
- `product_url`, `threshold`, `is_active`.
- last-known check state (`last_price`, `last_currency`, `last_checked_at`) to support app dashboards.

### `price_check_runs`
- Stores every check attempt, including errors.
- Enables observability and debugging without reading logs only.

### `auth_codes`
- Stores hashed OTP codes for email verification and phone 2FA.
- Includes purpose and expiry so flows can be validated safely.

### `auth_sessions`
- Stores hashed bearer tokens and expiry.
- Enables authenticated `/me/*` endpoints for frontend and mobile use.

## API routes included

Base docs: `GET /docs` (Swagger UI from FastAPI)

Implemented routes:
- `GET /health`
- `POST /auth/register/start`
- `POST /auth/register/verify-email`
- `POST /auth/register/verify-phone`
- `POST /auth/login/start`
- `POST /auth/login/verify`
- `GET /me`
- `POST /me/watchlist-items`
- `GET /me/watchlist-items`
- `PATCH /me/watchlist-items/{item_id}`
- `DELETE /me/watchlist-items/{item_id}`
- `POST /me/watchlist-items/{item_id}/check`
- `GET /me/watchlist-items/{item_id}/runs`

Legacy non-auth endpoints are still available for backward compatibility.

OTP verification endpoints include brute-force protection with configurable limits.

## Worker behavior

`plugin-boutique-worker` runs an infinite loop:
1. load all active watchlist items
2. run check for each
3. persist run rows
4. sleep (`WORKER_SLEEP_SECONDS`, default 300)

This is intentionally simple and understandable for a first deployment.

## Email/alert behavior

Runner checks SMTP env vars:
- `SMTP_ADDRESS`
- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`

If present and price is below threshold, it sends email.

If missing, it still records a successful price check, with a message that alert was skipped.

This lets you test API/worker without SMTP configured.

## How to run locally

From repo root:

```bash
uv sync
```

Start API:

```bash
uv run plugin-boutique-api
```

Start worker (new terminal):

```bash
uv run plugin-boutique-worker
```

Open docs:

```text
http://localhost:8000/docs
```

Open dashboard:

```text
http://localhost:8000/
```

Dashboard supports:
- registration with email + phone OTP
- login with phone OTP
- adding watchlist items
- updating threshold/active state
- deleting watchlist items
- running manual checks
- viewing run history

## Suggested local environment variables

```env
DATABASE_URL=sqlite:///./plugin_boutique.db
WORKER_SLEEP_SECONDS=300
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_ADDRESS=smtp.gmail.com
AUTH_DEV_MODE=true
DB_AUTO_CREATE=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+15551234567
```

`AUTH_DEV_MODE=true` is the recommended local setting. In this mode, OTP codes are returned in API responses and shown in the dashboard to make testing easy.

## Example auth + API flow (curl)

Start registration (dev mode returns `dev_code`):

```bash
curl -X POST http://localhost:8000/auth/register/start \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","phone_number":"+15551234567"}'
```

Verify email code:

```bash
curl -X POST http://localhost:8000/auth/register/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","code":"123456"}'
```

Verify phone code and get bearer token:

```bash
curl -X POST http://localhost:8000/auth/register/verify-phone \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","code":"654321"}'
```

Use token for watchlist operations:

```bash
curl -X GET http://localhost:8000/me/watchlist-items \
  -H "Authorization: Bearer <access_token>"
```

## How to connect a web frontend

Use any frontend stack (React/Next.js/Vue/etc.) and call the API endpoints above.

Minimal pages:
- user setup
- watchlist CRUD
- run history/status

Then add:
- pagination/filtering
- better run status UI

## How to connect a phone app

For React Native or Flutter:
- point app to this API
- store auth token once auth is added
- display watchlist + run history
- later add push notifications (APNs/FCM) for alerts

Do not run Selenium inside mobile apps.

## What is still scaffold-level (not production-ready yet)

This was built as a clear foundation, not a complete production system.

Missing pieces to add next:
1. Proper migrations (Alembic) instead of only `create_all`.
2. Real job queue (Celery/RQ/Arq/SQS) instead of polling loop.
3. Retry/backoff and concurrency controls.
4. Rate limiting and anti-blocking scraper strategy.
5. Structured logging + error monitoring.
6. Better secrets management and deployment configs.
7. Expand integration coverage to include more failure/retry paths and worker-loop scenarios.

## Implementation notes for learning

If you want to trace the code in reading order:
1. `web/settings.py`
2. `web/database.py`
3. `web/orm_models.py`
4. `web/schemas.py`
5. `web/scrape_runner.py`
6. `web/api.py`
7. `web/worker.py`

That order maps to:
- config -> storage -> data model -> API contracts -> business flow -> serving -> background processing.
