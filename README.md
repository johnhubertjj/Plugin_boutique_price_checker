# Plugin Boutique Price Tracker

Installable CLI for monitoring a Plugin Boutique product price and sending an email alert when the price falls below your threshold.

## Requirements

- Python 3.10+
- Google Chrome installed

## Install

### Option 1: Local project

```bash
pip install .
```

### Option 2: Editable (for development)

```bash
pip install -e .
```

After install, run the command:

```bash
plugin-boutique-alert \
  --url "https://www.pluginboutique.com/product/2-Effects/59-De-Esser/4392-Weiss-Deess" \
  --threshold 100 \
  --to "you@example.com"
```

## Multiple URLs and thresholds (JSON watchlist)

Create a JSON file (example: `watchlist.json`):

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

Run:

```bash
plugin-boutique-alert --watchlist-file "/absolute/path/to/watchlist.json" --to "default@example.com"
```

Notes:

- `to` is optional per item.
- `--to` acts as default recipient for any item missing `to`.
- If `--to` is not set, default recipient is `EMAIL_ADDRESS`.

## Environment variables

Set these in your shell or in a `.env` file:

- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`
- `SMTP_ADDRESS`

Example for Gmail SMTP:

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_ADDRESS=smtp.gmail.com
```

## Other ways to run

Run as module:

```bash
python -m amazon_scraper \
  --url "https://www.pluginboutique.com/product/2-Effects/59-De-Esser/4392-Weiss-Deess" \
  --threshold 100 \
  --to "you@example.com"
```

Run the compatibility wrapper from repo root:

```bash
python main.py \
  --url "https://www.pluginboutique.com/product/2-Effects/59-De-Esser/4392-Weiss-Deess" \
  --threshold 100 \
  --to "you@example.com"
```

Optional:

- `--no-headless` to open the browser UI.

## Run daily at a specific time

Use a scheduler so the command runs automatically once per day.

### macOS (`launchd`)

1. Find your installed CLI path:

```bash
which plugin-boutique-alert
```

2. Create `~/Library/LaunchAgents/com.example.pluginboutique.alert.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.example.pluginboutique.alert</string>
  <key>ProgramArguments</key>
  <array>
    <string>/ABSOLUTE/PATH/TO/plugin-boutique-alert</string>
    <string>--watchlist-file</string><string>/ABSOLUTE/PATH/TO/watchlist.json</string>
    <string>--to</string><string>you@example.com</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>EMAIL_ADDRESS</key><string>your_email@gmail.com</string>
    <key>EMAIL_PASSWORD</key><string>your_app_password</string>
    <key>SMTP_ADDRESS</key><string>smtp.gmail.com</string>
  </dict>
  <key>WorkingDirectory</key><string>/ABSOLUTE/PATH/TO/YOUR/PROJECT</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key><string>/tmp/pluginboutique-alert.out</string>
  <key>StandardErrorPath</key><string>/tmp/pluginboutique-alert.err</string>
</dict>
</plist>
```

3. Load and start it:

```bash
launchctl load ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl start com.example.pluginboutique.alert
```

4. Verify:

```bash
launchctl list | grep pluginboutique
```

Expected output (example):

```text
12345    0    com.example.pluginboutique.alert
```

Where:

- First column is the process ID (`-` if currently not running between schedule times).
- Second column is the last exit status (`0` means success).
- Third column is the LaunchAgent label.

### Update watchlist later (macOS)

If you buy an item and want to stop alerts for it, edit your `watchlist.json` and remove that entry.

If the watchlist path is unchanged, you usually do not need to regenerate the plist. Reload the LaunchAgent:

```bash
launchctl unload ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl load ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
```

If you changed schedule, label, or file paths, regenerate plist first, then reload:

```bash
python3 /ABSOLUTE/PATH/TO/plist_creator/create_plist.py ...your args...
launchctl unload ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl load ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
```

### Linux (`cron`)

1. Open crontab:

```bash
crontab -e
```

2. Add a daily job (example: 09:00 every day):

```cron
0 9 * * * EMAIL_ADDRESS=your_email@gmail.com EMAIL_PASSWORD=your_app_password SMTP_ADDRESS=smtp.gmail.com /ABSOLUTE/PATH/TO/plugin-boutique-alert --watchlist-file "/ABSOLUTE/PATH/TO/watchlist.json" --to "you@example.com" >> /tmp/pluginboutique-alert.log 2>&1
```

Notes:

- Always use absolute paths in schedulers.
- Test the command manually first before scheduling it.
- For plist debugging and common error fixes, see `docs/plist_troubleshooting.md`.
