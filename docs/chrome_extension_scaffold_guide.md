# Chrome Extension Scaffold Guide

A new Chrome extension scaffold now exists at:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension`

This scaffold is designed to reuse your existing backend API and auth model rather than duplicating business logic in the browser.

## What it does

- Connects to your FastAPI backend (`/auth/*`, `/me`, `/me/watchlist-items*`)
- Lets users register, verify OTP, login, and logout
- Manages watchlist items (create/list/check/delete)
- Stores API URL + token in `chrome.storage.local`
- Supports optional background auto-check by interval with Chrome alarms

## File map

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/manifest.json`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/popup.html`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/popup.css`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/popup.js`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/options.html`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/options.js`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/background.js`

## Local run steps

1. Start backend:

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker
uv run plugin-boutique-api
```

2. Load extension in Chrome:

- Open `chrome://extensions`
- Enable Developer mode
- Click **Load unpacked**
- Select `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension`

3. Open popup and save API URL:

- `http://127.0.0.1:8000` (typical local default)

4. Test auth flow in popup:

- Register start
- Verify email OTP
- Verify phone OTP
- Confirm `Authenticated: <email>` appears

5. Test watchlist:

- Add item
- Run check
- Delete item

If extension requests are blocked by CORS, add your extension origin to backend env:

- `CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,chrome-extension://<your-extension-id>`

## Production hardening before publish

1. Restrict `optional_host_permissions` in `manifest.json` to only your production API host.
2. Keep HTTPS-only API URL in production settings.
3. Publish a real privacy policy page (template: `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/PRIVACY_POLICY.md`).
4. Use separate dev/stage/prod API endpoints and credentials.
5. Follow full checklist: `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/docs/chrome_extension_production_checklist.md`.
