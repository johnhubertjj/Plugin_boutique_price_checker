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
    <string>--url</string><string>https://www.pluginboutique.com/product/...</string>
    <string>--threshold</string><string>100</string>
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

### Linux (`cron`)

1. Open crontab:

```bash
crontab -e
```

2. Add a daily job (example: 09:00 every day):

```cron
0 9 * * * EMAIL_ADDRESS=your_email@gmail.com EMAIL_PASSWORD=your_app_password SMTP_ADDRESS=smtp.gmail.com /ABSOLUTE/PATH/TO/plugin-boutique-alert --url "https://www.pluginboutique.com/product/..." --threshold 100 --to "you@example.com" >> /tmp/pluginboutique-alert.log 2>&1
```

Notes:

- Always use absolute paths in schedulers.
- Test the command manually first before scheduling it.
