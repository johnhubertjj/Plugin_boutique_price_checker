# plist Troubleshooting (macOS launchd)

This page covers common errors when creating/loading/running the LaunchAgent plist for `plugin-boutique-alert`.

## Quick health check

1. Validate plist syntax:

```bash
plutil -lint ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
```

2. Check load status:

```bash
launchctl list | grep pluginboutique
```

Expected format:

```text
<pid-or->    <last-exit-code>    com.example.pluginboutique.alert
```

- `pid`: `-` is normal between scheduled runs.
- `last-exit-code`: `0` means success.

3. Force a run:

```bash
launchctl kickstart -k gui/$(id -u)/com.example.pluginboutique.alert
```

4. Check logs:

```bash
tail -n 100 /tmp/pluginboutique-alert.out
tail -n 100 /tmp/pluginboutique-alert.err
```

## Common errors and fixes

### `Load failed: 5: Input/output error`

Likely causes:

- Invalid executable path in `ProgramArguments[0]`.
- Stale or conflicting LaunchAgent state.
- plist exists but points to paths that no longer exist.

Fix:

```bash
plutil -lint ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
```

### Exit code `78` in `launchctl list`

Meaning: job loaded, but runtime/config validation failed.

Most common causes:

- bad `--command-path` (for example `"."` instead of absolute executable path)
- missing `watchlist.json`
- invalid watchlist content
- missing `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, or `SMTP_ADDRESS`

Fix checklist:

1. Open plist and verify `ProgramArguments[0]` is absolute executable path.
2. Manually run the exact command from `ProgramArguments`.
3. Verify watchlist exists and validates.

### `plugin-boutique-alert` not found

Cause: command is not on shell PATH or not installed in system location.

Fix:

- Use absolute executable path from your virtualenv or install location.
- Example:
  `/Users/<you>/.../.venv/bin/plugin-boutique-alert`

### No output in log files

Possible causes:

- Job did not run yet.
- Log file paths differ from what you are tailing.
- Early launch failure before process starts.

Fix:

1. Run `launchctl kickstart -k ...` to force execution.
2. Check `StandardOutPath` and `StandardErrorPath` values in plist.
3. Use `launchctl print gui/$(id -u)/com.example.pluginboutique.alert` for runtime details.

### Watchlist validation errors

`create_plist.py` enforces:

- file exists
- `.json` extension
- non-empty JSON array
- each item has non-empty `url` and numeric `threshold`

Fix invalid entries in `watchlist.json` and regenerate plist.

### Gmail authentication errors

Cause: wrong password type or revoked password.

Fix:

- use Google App Password (not normal account password)
- regenerate App Password if exposed or no longer working

## Safe regenerate/reload workflow

```bash
python3 /ABSOLUTE/PATH/TO/plist_creator/create_plist.py ...your args...
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.pluginboutique.alert.plist
launchctl kickstart -k gui/$(id -u)/com.example.pluginboutique.alert
launchctl list | grep pluginboutique
```

## Security note

If an app password was shared in chat, logs, screenshots, or committed to source:

1. Revoke it immediately in Google account security settings.
2. Generate a new app password.
3. Update plist or environment values with the new password.
