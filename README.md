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
