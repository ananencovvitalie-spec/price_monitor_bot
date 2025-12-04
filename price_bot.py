# price_bot.py
import asyncio
import json
import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")     # Token-ul botului din variabile de mediu
CHANNEL = os.environ.get("CHANNEL")     # @channel
DB_FILE = "db.json"
CHECK_INTERVAL_SECONDS = 86400          # O dată pe zi

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

# --- Extract price (NO Playwright) ---
async def extract_price(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        texts = soup.find_all(text=True)

        prices = []
        for t in texts:
            txt = t.strip()

            # Cautăm texte care conțin cifre
            if any(ch.isdigit() for ch in txt):
                clean = "".join(ch for ch in txt if ch.isdigit())
                if clean.isdigit() and len(clean) >= 3:       # prețuri min 3 cifre
                    prices.append(int(clean))

        if not prices:
            return None

        # Returnăm cel mai mic preț găsit (de obicei prețul real)
        return min(prices)

    except Exception as e:
        print("Eroare scraping:", e)
        return None

# --- Price check logic ---
async def check_prices():
    bot = Bot(TOKEN)
    db = load_db()

    for url, old_price in db.items():
        current_price = await extract_price(url)
        if current_price is None:
            continue

        if current_price < old_price:
            msg = (
                f"📉 *Preț redus!*\n\n"
                f"Vechea valoare: {old_price} lei\n"
                f"Noua valoare: {current_price} lei\n\n"
                f"{url}"
            )
            await bot.send_message(CHANNEL, msg, parse_mode="Markdown")
            db[url] = current_price

    save_db(db)

# --- Add product manually ---
async def add_product(url, price):
    db = load_db()
    db[url] = int(price)
    save_db(db)

    bot = Bot(TOKEN)
    await bot.send_message(
        CHANNEL,
        f"✅ Produs adăugat pentru monitorizare:\n{url}\nPreț inițial: {price} lei"
    )

# --- Main loop ---
async def main():
    print("Bot pornit și rulează...")
    while True:
        await check_prices()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())
