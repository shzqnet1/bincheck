import asyncio
import logging
import os
import sys
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5194696458]

if not API_TOKEN:
    print("Ошибка: переменная окружения BOT_TOKEN не задана!")
    sys.exit(1)

# ================== LOGGING ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== CACHE ==================
BIN_CACHE = {}

# ================== COUNTRY FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== BIN CHECKER ==================
def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())
    if len(bin_number) < 6:
        return "❌ Введи корректный BIN — минимум 6 цифр."
    bin_number = bin_number[:6]

    if bin_number in BIN_CACHE:
        return BIN_CACHE[bin_number]

    # Список API (резервный на случай сбоя Binlist)
    api_urls = [
        f"https://lookup.binlist.net/{bin_number}",
        f"https://bins.antipublic.cc/bins/{bin_number}"
    ]

    for url in api_urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            country_code = data.get('country', {}).get('alpha2', '') or data.get('country', '')
            flag = country_flag(country_code)
            response = (
                f"💳 **BIN:** `{bin_number}`\n"
                f"🏦 **Банк:** {data.get('bank', {}).get('name', 'N/A')}\n"
                f"🌍 **Страна:** {flag}\n"
                f"💼 **Тип:** {data.get('type', 'N/A')}\n"
                f"💳 **Система:** {data.get('scheme', 'N/A')}\n"
                f"🏷 **Бренд:** {data.get('brand', 'N/A')}"
            )
            BIN_CACHE[bin_number] = response
            return response
        except Exception:
            continue
    return "❌ BIN не найден или недействителен."

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в топ BIN Checker Bot!\n\n"
        "🔹 Используй команду /bin <номер карты> или !bin <номер карты> для проверки.\n"
        "Пример: /bin 4165985824414481 или !bin 457173XXXXXX"
    )

@dp.message()
async def bin_message_handler(message: types.Message):
    text = (message.text or "").strip()
    if text.startswith("/bin"):
        args = text[4:].strip()
    elif text.startswith("!bin"):
        args = text[4:].strip()
    else:
        return
    if not args:
        await message.answer("❌ Укажи BIN после команды, например: /bin 457173 или !bin 457173")
        return
    response = bin_lookup(args)
    await message.answer(response, parse_mode="Markdown")

# ================== RUN BOT ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
