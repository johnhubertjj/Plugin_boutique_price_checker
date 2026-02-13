# Mobile App Scaffold (Expo React Native)

This is a starter mobile app wired to the existing backend API.

## Features included

- Register flow (email + phone OTP)
- Login flow (phone OTP)
- Secure token storage (`expo-secure-store`)
- Authenticated watchlist list/create/run-check/delete

## Prerequisites

- Node.js 18+
- npm
- Expo CLI (via `npx expo` is enough)
- Backend API running (`uv run plugin-boutique-api`)

## Configure API URL

Copy `.env.example` to `.env` and set the base URL:

```bash
cp .env.example .env
```

Examples:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Physical device: use your machine LAN IP, e.g. `http://192.168.1.50:8000`

## Run

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app
npm install
npx expo start
```

Then press:

- `a` for Android emulator
- `i` for iOS simulator (macOS + Xcode)

## Notes

- In dev backend mode (`AUTH_DEV_MODE=true`), OTP codes are returned and displayed.
- In production backend mode (`AUTH_DEV_MODE=false`), real SMTP/Twilio delivery is required.
