# Chrome Extension Screenshot Checklist

Use this checklist to create clear Web Store screenshots from the current extension.

## Setup

1. Start backend API and verify extension is loaded unpacked.
2. Use a clean test account and realistic watchlist URLs.
3. Keep screenshots consistent (same browser zoom, window size, and theme).

## Required Capture Set (Recommended)

1. Popup after successful authentication
- Show: authenticated state and basic status area.

2. Registration + OTP flow
- Show: register form and OTP input forms.
- Avoid exposing real phone numbers or real OTP values.

3. Watchlist management
- Show: at least 2 watchlist items, plus Run Check and Delete actions.

4. Options page configuration
- Show: API URL field and auto-check interval.

5. Permission prompt context
- Show: host permission flow after saving API URL (if possible in your capture flow).

6. Background-check behavior evidence
- Show: option enabled and an example notification result.

## Quality Checks

1. No secrets or tokens visible.
2. No personal email/phone in final images.
3. Text in screenshots is readable at a glance.
4. Images reflect current UI and permissions behavior.

## File Naming Convention

Use deterministic names for easier updates:

- `01-authenticated-popup.png`
- `02-registration-otp-flow.png`
- `03-watchlist-management.png`
- `04-options-page.png`
- `05-host-permission-flow.png`
- `06-background-notification.png`

## Final Pre-Submit Pass

1. Verify screenshots match the shipped extension version.
2. Re-capture if UI changed after hardening.
3. Confirm screenshot count and dimensions against current Chrome Web Store dashboard requirements.
