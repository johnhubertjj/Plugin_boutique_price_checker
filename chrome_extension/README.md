# Chrome Extension Scaffold

This folder contains a Manifest V3 extension scaffold for your existing FastAPI backend.

## Included features

- Configure API base URL (`popup` and `options`)
- Runtime origin permission request for the configured API host only
- Registration flow (email OTP + phone OTP)
- Login flow (2FA phone OTP)
- Save bearer token in `chrome.storage.local`
- Automatically clears auth token if API host is changed
- List, create, run-check, and delete watchlist items
- Optional background auto-check alarm (interval in options)

## Load in Chrome

1. Start backend API from repo root:

```bash
uv run plugin-boutique-api
```

2. Open Chrome and go to:

- `chrome://extensions`

3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select this folder:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension`

6. Open extension popup and set API URL:

- Local API default: `http://127.0.0.1:8000`

## Notes

- In backend dev mode (`AUTH_DEV_MODE=true`), OTP codes are returned in API responses and shown in popup.
- For production, set `AUTH_DEV_MODE=false` and configure SMTP + Twilio on backend.
- The extension now uses `optional_host_permissions` and asks for host access only when you save API URL.
- If your browser blocks requests, include your extension origin in backend CORS, for example:
  `CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,chrome-extension://<your-extension-id>`
- For publish hardening checklist, see:
  `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/docs/chrome_extension_production_checklist.md`

## Build a release zip

From repo root:

```bash
./scripts/package_chrome_extension.sh
```

Output goes to:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/dist/chrome_extension/`
