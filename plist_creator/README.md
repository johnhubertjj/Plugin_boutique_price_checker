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
