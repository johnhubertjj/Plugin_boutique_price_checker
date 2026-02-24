# Full Change Audit, Code Walkthrough, and State Recovery

This document is a full reconstruction of the work completed in this session, including:

1. Prompt-by-prompt tasks performed.
2. File-level changes.
3. Line-by-line behavior walkthrough for core code files.
4. Snapshot artifacts to recover available repository states.

## Important limitation up front

You asked for saved states "at that time" for each prompt.

Because changes were not committed as we went, exact intermediate states cannot be perfectly reconstructed now.
What I can reliably provide:

- Baseline tracked repo state at `HEAD` before current uncommitted worktree changes.
- Current full working-tree state.

These are packaged under `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/snapshots`.

## Snapshot artifacts created

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/snapshots/000_head_baseline_eb245da.tar.gz`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/snapshots/001_current_working_tree.tar.gz`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/snapshots/SHA256SUMS.txt`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/snapshots/README.md`

## Prompt-by-prompt timeline (what changed)

1. **Rename remaining `amazon_scraper` references**
- Found one content reference in `__main__.py`.
- Updated module run hint string to `plugin_boutique_price_checker`.

2. **Full package rename request**
- Renamed `src/amazon_scraper` -> `src/plugin_boutique_price_checker`.
- Renamed egg-info and IDE module file path names.
- Re-ran tests; imports remained valid.

3. **Coverage check request**
- Measured coverage and reported weak areas (`__main__.py`, `cli.py`, `selenium_scraper.py`).

4. **Focused tests request**
- Added/expanded tests for CLI, module entrypoint, and Selenium behavior.
- Coverage improved to 99%.

5. **Deployable scaffold request (web/app path)**
- Added API scaffold, DB models, worker process, and docs.
- Added API/worker CLI entrypoints.

6. **Minimal frontend request**
- Added static dashboard served by FastAPI.
- Wired CRUD/check/run-history from browser JS.

7. **Switch docs/install flow from `pip` to `uv`**
- Updated README and docs commands to `uv sync` / `uv run`.

8. **Frontend bug reports (create user/null reset/favicon noise)**
- Fixed async form/null target bug.
- Improved duplicate-user UX handling.
- Added `/favicon.ico` no-content route to reduce noise.

9. **Remove watchlist item button request**
- Added API delete endpoint.
- Added dashboard Remove button with confirm.

10. **Auth request (email validation + phone 2FA + dev test mode)**
- Added auth models/tables and OTP/session logic.
- Added registration/login OTP flows.
- Added authenticated `/me/*` endpoints.
- Updated frontend auth UI flow.

11. **Beginner guide + auth/integration tests + brute-force protection**
- Added beginner guide doc.
- Added API integration tests for auth and `/me` flows.
- Added OTP brute-force lockout controls.

12. **Real SMS delivery request**
- Implemented Twilio REST send path.
- Added SMS unit tests.

13. **SQLite duplicate column startup bug**
- Fixed schema compatibility probe (PRAGMA name index).

14. **Production readiness + GCP deployment + cost request**
- Added production hardening (CORS, readiness, logout, cookie auth option, DB auto-create toggle).
- Added Alembic migrations.
- Added Dockerfiles.
- Added Cloud Build + deployment scripts + scheduler scripts.
- Added optional Terraform scaffold.
- Added GCP runbook and cost estimate docs.

## Top-level files changed/added

Core app/deploy files:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/api.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/auth.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/database.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/orm_models.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/settings.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/schemas.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/scrape_runner.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/worker.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/static/index.html`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/static/styles.css`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/src/plugin_boutique_price_checker/web/static/app.js`

Migrations/deploy/infra/docs/tests:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/alembic.ini`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/alembic/env.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/alembic/versions/20260212_0001_initial_schema.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/Dockerfile.api`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/Dockerfile.worker`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/cloudbuild.yaml`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/deploy/gcp/*.sh`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/infra/terraform/*`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/tests/test_api_auth_integration.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/tests/test_auth_sms.py`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/docs/*.md` (new guides/runbooks/cost/audit)

## Line-by-line behavior walkthrough (core code)

Note: to keep this readable, this uses **line-range behavior mapping** (near line-by-line).
Generated artifacts (`uv.lock`, DB files) are summarized separately.

### `src/plugin_boutique_price_checker/web/api.py`

- `1-14`: imports FastAPI, SQLAlchemy, response/static types.
- `15-45`: imports app-local auth/db/schema dependencies.
- `46-59`: creates app, dependency aliases, static mount, CORS policy.
- `62-67`: startup hook; optional auto table creation controlled by `DB_AUTO_CREATE`.
- `69-79`: liveness and readiness endpoints.
- `82-91`: serves dashboard and responds to favicon route.
- `94-102`: helper to set secure/httponly auth cookie.
- `105-127`: registration start endpoint; upsert user identity and issue email OTP.
- `129-160`: verify email OTP, apply brute-force guard, then issue phone OTP.
- `163-190`: verify phone OTP, mark 2FA enabled, create session token/cookie.
- `192-208`: login start endpoint issuing login 2FA OTP.
- `210-230`: login verify endpoint with OTP checks and session issuance.
- `233-248`: logout endpoint; revokes session and clears cookie.
- `251-254`: `GET /me` authenticated user profile.
- `257-268`: legacy direct user creation endpoint.
- `271-344`: authenticated watchlist CRUD/check/history endpoints under `/me`.
- `347-416`: legacy non-auth watchlist routes for compatibility.
- `418+`: legacy non-auth manual check and runs endpoints.

### `src/plugin_boutique_price_checker/web/auth.py`

- `21-29`: hashing and OTP generation helpers.
- `31-45`: creates `AuthCode` rows with expiry.
- `48-71`: validates and consumes OTP code (one-time use).
- `74-85`: creates bearer session token row.
- `88-97`: revokes bearer sessions.
- `99-107`: helper key/timestamp normalization utilities.
- `110-115`: block check (429 when blocked).
- `118-140`: failure counter windowing and temporary blocking.
- `143-150`: clears OTP failure tracker on success.
- `153-167`: sends email OTP via SMTP.
- `170-202`: sends phone OTP through Twilio REST API.
- `205-237`: resolves current user from Bearer header or cookie token.

### `src/plugin_boutique_price_checker/web/orm_models.py`

- `11-13`: UTC timestamp utility.
- `16-32`: `User` table, identity + verification + relationships.
- `34-57`: `WatchlistItem` table, thresholds + last check metadata.
- `59-74`: `PriceCheckRun` audit table for each check execution.
- `76-91`: `AuthCode` OTP storage (hashed code, purpose, expiry, consumed).
- `93-106`: `AuthSession` token table (hashed token, expiry/revoke).
- `108-123`: `OtpAttempt` brute-force tracker table.

### `src/plugin_boutique_price_checker/web/settings.py`

- `7-30`: typed settings object fields.
- `32-37`: parses comma-separated CORS origins.
- `40-66`: loads all env vars, applies defaults, parses booleans.

### `src/plugin_boutique_price_checker/web/database.py`

- `10-20`: SQLAlchemy base, engine/session creation.
- `23-29`: table creation entrypoint.
- `31-50`: SQLite compatibility patching for legacy `users` columns.

### `src/plugin_boutique_price_checker/web/schemas.py`

- `8-12`: `UserCreate` input.
- `14-26`: `UserRead` output (includes verification fields).
- `28-58`: watchlist create/update/read schemas.
- `60-73`: run history schema.
- `75-107`: auth request/response payload schemas.

### `src/plugin_boutique_price_checker/web/scrape_runner.py`

- `13-21`: builds notifier only if SMTP config exists.
- `24-72`: one full check lifecycle (scrape, compare, notify, persist run).
- `75-84`: helper running check by item id with managed session.

### `src/plugin_boutique_price_checker/web/worker.py`

- `14-25`: run active items once.
- `28-46`: main loop; supports one-shot mode (`WORKER_RUN_ONCE=true`) and recurring poll mode.

### `src/plugin_boutique_price_checker/web/static/index.html`

- Defines dashboard structure:
  - registration/email/phone verification forms
  - login forms
  - watchlist create/list/update/delete controls
  - run history panel
  - status/toast container

### `src/plugin_boutique_price_checker/web/static/styles.css`

- Defines theme tokens, responsive grid/card layout, form/button styling, status toasts, mobile breakpoints.

### `src/plugin_boutique_price_checker/web/static/app.js`

- `1-13`: global state and key DOM handles.
- `15-41`: helpers for status toasts, token persistence, auth status rendering.
- `43-65`: `request()` wrapper with auth header and JSON/error handling.
- `67-207`: data rendering/loading for watchlist and run panels.
- `209-303`: registration/login OTP flow handlers.
- `305-318`: logout flow (server revoke + client state clear).
- `320-353`: create watchlist and refresh handlers.
- `355-362`: app init.

### `tests/test_api_auth_integration.py`

- temp isolated DB fixture + module reload.
- full registration/login flow tests.
- authenticated `/me/watchlist-items` CRUD tests.
- OTP brute-force lockout test.
- logout/session invalidation test.

### `tests/test_auth_sms.py`

- validates Twilio SMS sender prerequisites.
- validates Twilio request payload construction (from number vs messaging service SID).
- validates error handling for failed Twilio responses.

## Deployment and infra files (what each line category does)

### Docker and Cloud Build

- `Dockerfile.api`: installs runtime dependencies + Chromium stack, copies app, starts Uvicorn on `8080`.
- `Dockerfile.worker`: same base dependencies, starts worker command, defaults to one-shot mode.
- `cloudbuild.yaml`: build/push images, deploy API, deploy+run migration job, deploy worker job.

### GCP scripts

- `deploy/gcp/bootstrap_gcp.sh`: enable required APIs + create Artifact Registry repository.
- `deploy/gcp/create_secrets.sh`: create Secret Manager placeholders.
- `deploy/gcp/deploy_via_cloud_build.sh`: run Cloud Build with substitutions.
- `deploy/gcp/create_worker_scheduler.sh`: create/update Cloud Scheduler HTTP trigger to run worker job.

### Terraform scaffold

- `infra/terraform/main.tf`: optional IaC for APIs, Artifact Registry, Cloud SQL, service accounts, secrets, Cloud Run service/job, scheduler.
- `infra/terraform/variables.tf`: parameter definitions.
- `infra/terraform/outputs.tf`: emitted resource outputs.
- `infra/terraform/terraform.tfvars.example`: starter values.

### Alembic

- `alembic/env.py`: migration runtime configuration using project settings.
- `alembic/versions/20260212_0001_initial_schema.py`: initial DDL for users/watchlist/runs/auth/totp attempt tables and indexes.

## Files that are generated or data-heavy (not practical for literal line-by-line prose)

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/uv.lock`
  - generated dependency lock metadata; each line pins package resolution state.
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/plugin_boutique.db`
  - runtime SQLite data file; binary-ish database pages, not source code.

## Recommended next step to avoid this recovery issue again

Use frequent local checkpoints:

1. `git add -A`
2. `git commit -m "milestone: <what changed>"`

Even if temporary, this preserves exact states and makes "restore this point" trivial.

