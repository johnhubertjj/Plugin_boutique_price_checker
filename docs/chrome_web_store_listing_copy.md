# Chrome Web Store Listing Copy (Template)

Use this as your baseline listing copy, then edit for your branding before submission.

## Extension Name

Plugin Boutique Price Checker

## Summary (short description)

Track Plugin Boutique prices with secure login, watchlist management, and optional background checks.

## Full Description

Plugin Boutique Price Checker helps you monitor product prices from your own backend service.

### What you can do

- Register and sign in with email + phone OTP verification
- Add, view, run, and remove watchlist items
- Trigger manual checks on demand
- Optionally enable timed background checks

### How it works

- The extension connects to your configured API endpoint.
- Authentication and watchlist actions are processed by your backend.
- The extension stores minimal local settings in Chrome storage (API URL, token, email, interval).

### Security highlights

- Host access is requested at runtime only for your chosen API origin
- Content Security Policy blocks remote script execution on extension pages
- Auth is cleared automatically when API host is changed

### Important notes

- This extension requires a compatible backend deployment.
- In production, use HTTPS and disable dev OTP mode on the backend.

## Category Suggestion

Developer Tools or Productivity

## Support URL (suggestion)

Use your project docs page, for example:

- https://github.com/<your-org>/<your-repo>

## Privacy Policy URL

Publish a public HTTPS page based on:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/PRIVACY_POLICY.md`

## Store Submission Notes (for reviewer)

- The extension requests host permission only after user configures API URL.
- Authentication requires backend endpoints under `/auth/*`.
- Watchlist actions use `/me/watchlist-items*` endpoints.
