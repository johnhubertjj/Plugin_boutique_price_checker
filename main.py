import os

from bs4 import BeautifulSoup
import requests
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")
receiver_address = 'john.hubert12@gmail.com'
WEBSITE = 'https://www.pluginboutique.com/products/4392-Weiss-Deess'


import re

url = "https://www.pluginboutique.com/product/2-Effects/59-De-Esser/4392-Weiss-Deess"
headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"}

r = requests.get(url, headers=headers)
html = r.text

# Find a nearby “anchor” so we don’t accidentally grab some other price (like a recommended product)
anchor = html.lower().find("add to cart")
if anchor == -1:
    anchor = html.lower().find("buy now")

# Find all currency-looking prices
matches = list(re.finditer(r'([£€$])\s?(\d[\d,]*(?:\.\d{2})?)', html))

if not matches:
    raise RuntimeError("No currency-like prices found in HTML")

# Pick the one closest to the “Add to Cart” / “Buy Now” area
best = min(matches, key=lambda m: abs(m.start() - anchor) if anchor != -1 else m.start())

currency = best.group(1)
amount = best.group(2)
amount_to_compare = float(amount)
price = f"{currency}{amount}"
print("Price:", price)

if amount_to_compare > 100:
    contents = (f'The Weiss De-esser ({url}) is below £100!!! \n '
                f'it now costs {price}!')

    msg = EmailMessage()
    msg["Subject"] = "Plugin Boutique price alert"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_address
    msg.set_content(contents)

    print(contents)
    with smtplib.SMTP_SSL(SMTP_ADDRESS, 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)
