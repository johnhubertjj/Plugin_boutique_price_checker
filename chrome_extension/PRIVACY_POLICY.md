# Privacy Policy (Template)

Last updated: 2026-02-13

This extension helps users authenticate against a backend service and manage Plugin Boutique watchlist items.

## Data processed

- Email address (for authentication)
- Phone number (for 2FA during registration/login)
- Watchlist item URLs and thresholds
- API access token (stored in Chrome local extension storage)

## How data is used

- To authenticate users through the configured backend API
- To create/list/update/delete watchlist items
- To run background checks when enabled by the user

## Data sharing

- Data is sent only to the backend API URL configured by the user.
- The extension does not sell personal data.

## Local storage

The extension stores the following locally via `chrome.storage.local`:

- API base URL
- Access token
- Last auth email
- Auto-check interval

## Security controls

- Runtime API host permission is requested only for configured API origin.
- Content Security Policy restricts extension pages to local scripts.

## User controls

- Users can log out to remove active session token from local storage.
- Users can remove watchlist entries from the extension UI.

## Contact

Replace this section with your support email or support page before publish.
