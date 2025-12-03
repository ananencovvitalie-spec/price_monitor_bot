# price_bot.py
import asyncio
import json
import datetime
import os
from playwright.async_api import async_playwright
from telegram import Bot

# --- CONFIG ---
TOKEN = os.environ.get("8452580567:AAG599O3xJY70a8ex3dI-qe3caG8tswqv_k")   # vom pune token-ul ca variabila de mediu
CHANNEL = os.environ.get("@price_monitoring_2025")   # username-ul canalului sau ID numeric
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
async def extract_price(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(2500)  # așteaptă să încarce prețul

        selectors = [".product-price", ".price", ".product__price", "span.price", ".woocommerce-Price-amount"]
        text = None
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.inner_text()
                    if text and any(ch.isdigit() for ch in text):
                        break
            except:
                continue

        if not text:
            await browser.close()
            return None

        clean = "".join(ch for ch in text if ch.isdigit())
        await browser.close()
        return int(clean) if clean else None

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
