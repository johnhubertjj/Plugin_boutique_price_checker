# plist_creator

Small utility to generate a macOS `launchd` plist for `plugin-boutique-alert`.

## What it asks for

- `plugin-boutique-alert` executable location
- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`
- `SMTP_ADDRESS`

It can also set schedule, URL, threshold, and recipient email.

## Usage

```bash
python3 create_plist.py \
  --command-path "/absolute/path/to/plugin-boutique-alert" \
  --email-address "your_email@gmail.com" \
  --email-password "your_google_app_password" \
  --smtp-address "smtp.gmail.com" \
  --url "https://www.pluginboutique.com/product/..." \
  --threshold 100 \
  --to "you@example.com" \
  --hour 9 \
  --minute 0 \
  --output "~/Library/LaunchAgents/com.example.pluginboutique.alert.plist" \
  --label "com.example.pluginboutique.alert"
```

If `--to` is not provided, it defaults to `--email-address`.

## Multiple URLs and thresholds with JSON

Create a watchlist JSON file:

```json
[
  {
    "url": "https://www.pluginboutique.com/product/2-Effects/59-De-Esser/4392-Weiss-Deess",
    "threshold": 100,
    "to": "alerts1@example.com"
  },
  {
    "url": "https://www.pluginboutique.com/product/1-Instruments/4-Synth/1234-Example",
    "threshold": 49.99
  }
]
```

Then generate plist in watchlist mode:

```bash
python3 create_plist.py \
  --command-path "/absolute/path/to/plugin-boutique-alert" \
  --email-address "your_email@gmail.com" \
  --email-password "your_google_app_password" \
  --smtp-address "smtp.gmail.com" \
  --watchlist-file "/absolute/path/to/watchlist.json" \
  --to "default@example.com" \
  --hour 9 \
  --minute 0
```

Watchlist notes:

- Each item must include `url` and `threshold`.
- Item-level `to` is optional.
- `--to` is used as default recipient when an item omits `to`.

## Load and run

```bash
launchctl load ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl start com.example.pluginboutique.alert
launchctl list | grep pluginboutique
```

## Google App Password setup (Gmail)

Gmail SMTP should use an App Password, not your normal account password.

1. Turn on 2-Step Verification on your Google account.
2. Open your Google Account settings.
3. Go to `Security`.
4. Open `App passwords`.
5. Choose app `Mail` and device `Other` (or any label you want), then generate.
6. Use the generated 16-character password as `EMAIL_PASSWORD`.

Notes:

- If `App passwords` is missing, 2-Step Verification is usually not enabled yet.
- Some Google Workspace admins disable App Passwords.
