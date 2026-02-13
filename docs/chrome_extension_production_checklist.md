# Chrome Extension Production Checklist

Use this checklist before Chrome Web Store submission.

## Security

1. Restrict extension host access:
- In `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/manifest.json`, replace broad optional host patterns with your real API origin(s).
- Example: `https://api.yourdomain.com/*`

2. Enforce HTTPS only:
- In production, set API URL to `https://...` only.
- Do not allow plaintext HTTP outside local development.

3. Limit backend CORS:
- Set backend `CORS_ALLOWED_ORIGINS` to exact origins only.
- Include extension origin: `chrome-extension://<extension-id>`

4. Keep OTP dev mode off:
- Set backend `AUTH_DEV_MODE=false` in production.
- Verify SMTP + Twilio credentials are set and rotated.

5. Token and session handling:
- Keep token lifetime bounded (`AUTH_SESSION_TTL_HOURS`).
- Revoke on logout.
- Consider adding refresh-token rotation server-side for long sessions.

## Reliability

1. Use separate environments:
- Dev, staging, production with separate API URLs and secrets.

2. Add monitoring:
- Track auth failures, OTP rate-limit events, and 5xx API responses.

3. Add error reporting:
- Add extension-side error analytics (without collecting sensitive OTP/token values).

## Compliance and Store Readiness

1. Provide a privacy policy page:
- Start from `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/chrome_extension/PRIVACY_POLICY.md`.
- Publish as a public HTTPS page and link it in Web Store listing.

2. Complete store listing assets:
- 16/32/48/128 icons
- Screenshots
- Description and support contact

3. Permission justification:
- Explain why `storage`, `alarms`, `notifications`, and host access are needed.

4. Store listing copy:
- Use and adapt: `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/docs/chrome_web_store_listing_copy.md`.

5. Screenshot pack:
- Capture against: `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/docs/chrome_extension_screenshot_checklist.md`.

## Test Gates Before Release

1. Manual flows:
- Register -> email OTP -> phone OTP -> login -> add item -> run check -> delete item -> logout

2. Background flow:
- Enable auto-check interval and verify alarm-triggered checks.

3. Failure cases:
- Wrong OTP, expired OTP, blocked OTP (rate limit), API down, CORS misconfig.

4. Browser compatibility:
- Test latest stable Chrome.

## Packaging

Build upload zip from repo root:

```bash
./scripts/package_chrome_extension.sh
```

Archive output:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/dist/chrome_extension/`
