import asyncio
import logging
import os
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5194696458]

if not API_TOKEN:
    print("Ошибка: переменная окружения BOT_TOKEN не задана!")
    exit(1)

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

# ================== BIN API ==================
async def fetch_bin_info(bin_number: str):
    url = f"https://binlist.io/lookup/{bin_number}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

async def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())

    if len(bin_number) < 6:
        return "❌ Введи корректный BIN — минимум 6 цифр."

    bin_number = bin_number[:6]

    # Проверка кэша
    if bin_number in BIN_CACHE:
        return BIN_CACHE[bin_number]

    data = await fetch_bin_info(bin_number)

    if not data:
        return "❌ BIN не найден."

    bank = data.get("bank", {}).get("name", "N/A")
    country = data.get("country", {}).get("code", "")
    scheme = data.get("scheme", "N/A")
    brand = data.get("brand", "N/A")
    type_ = data.get("type", "N/A")

    flag = country_flag(country)

    response = (
        f"💳 **BIN:** `{bin_number}`\n"
        f"🏦 **Банк:** {bank}\n"
        f"🌍 **Страна:** {flag}\n"
        f"💼 **Тип:** {type_}\n"
        f"💳 **Система:** {scheme}\n"
        f"🏷 **Бренд:** {brand}"
    )

    BIN_CACHE[bin_number] = response
    return response

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Это BIN Checker Bot\n\n"
        "Используй:\n"
        "/bin 457173\n"
        "или\n"
        "!bin 457173"
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
        await message.answer("❌ Укажи BIN. Пример: /bin 457173")
        return

    response = await bin_lookup(args)
    await message.answer(response, parse_mode="Markdown")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
