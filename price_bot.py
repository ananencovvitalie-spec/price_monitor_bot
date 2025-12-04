# price_bot.py
import asyncio
import json
import datetime
import os
from playwright.async_api import async_playwright
from telegram import Bot

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")   # vom pune token-ul ca variabila de mediu
CHANNEL = os.environ.get("CHANNEL")   # username-ul canalului sau ID numeric
DB_FILE = "db.json"
CHECK_INTERVAL_SECONDS = 86400  # verifică o dată pe zi

# --- DB helpers ---
def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Price extractor ---
import requests
from bs4 import BeautifulSoup

async def extract_price(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Căutăm toate elementele care conțin "lei" sau cifre
        possible = soup.find_all(text=True)

        prices = []
        for text in possible:
            txt = text.strip()
            if "lei" in txt.lower() or any(ch.isdigit() for ch in txt):
                clean = "".join(ch for ch in txt if ch.isdigit())
                if clean.isdigit():
                    prices.append(int(clean))

        if not prices:
            return None

        return min(prices)  # cel mai mic preț găsit
    except:
        return None

# --- Bot logic ---
async def check_prices():
    bot = Bot(TOKEN)
    db = load_db()

    for url, old_price in db.items():
        current_price = await extract_price(url)
        if current_price is None:
            continue

        if current_price < old_price:
            msg = f"📉 *Preț redus!*\n\nVechea valoare: {old_price} lei\nNoua valoare: {current_price} lei\n{url}"
            await bot.send_message(CHANNEL, msg, parse_mode="Markdown")
            db[url] = current_price

    save_db(db)

# --- Add product ---
async def add_product(url, price):
    db = load_db()
    db[url] = int(price)
    save_db(db)
    bot = Bot(TOKEN)
    await bot.send_message(CHANNEL, f"✅ Produs adăugat pentru monitorizare:\n{url}\nPreț inițial: {price} lei")

# --- Loop principal ---
async def main():
    while True:
        await check_prices()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())
