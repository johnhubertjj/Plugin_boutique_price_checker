# Mobile Scaffold Guide (Expo + React Native)

This project now includes a mobile scaffold at:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app`

## What is included

- Registration flow (email OTP + phone OTP)
- Login flow (phone OTP)
- Secure token persistence with `expo-secure-store`
- Authenticated watchlist operations:
  - list items
  - create item
  - run check
  - delete item

## Key files

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app/App.tsx`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app/src/api/client.ts`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app/src/auth/session.ts`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app/src/types/api.ts`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app/src/config/index.ts`

## Run locally

1. Start backend API:

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker
uv run plugin-boutique-api
```

2. Configure mobile API URL:

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/mobile_app
cp .env.example .env
```

Set `EXPO_PUBLIC_API_BASE_URL`:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Physical device: `http://<your-lan-ip>:8000`

3. Run app:

```bash
npm install
npx expo start
```

## Next mobile-ready steps

1. Add navigation stack/tabs and split screens.
2. Add refresh token flow.
3. Add push notifications with Firebase Cloud Messaging.
4. Add API pagination and optimistic updates.
5. Add E2E tests (Detox or Maestro) for auth/watchlist flows.

