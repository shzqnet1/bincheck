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

# ================== COUNTRY FLAG ==================
def country_flag(country_code: str) -> str:
    """Преобразует двухбуквенный код страны в emoji флаг"""
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== BIN CHECKER ==================
def bin_lookup(bin_number: str) -> str:
    url = f"https://lookup.binlist.net/{bin_number}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return "❌ BIN не найден или недействителен."
        data = r.json()
        country_code = data.get('country', {}).get('alpha2', '')
        return (
            f"💳 BIN: {bin_number[:6]}\n"
            f"🏦 Банк: {data.get('bank', {}).get('name', 'N/A')}\n"
            f"🌍 Страна: {data.get('country', {}).get('name', 'N/A')} {country_flag(country_code)}\n"
            f"💼 Тип: {data.get('type', 'N/A')}\n"
            f"💳 Система: {data.get('scheme', 'N/A')}\n"
            f"🏷 Бренд: {data.get('brand', 'N/A')}"
        )
    except Exception:
        return "⚠️ Ошибка при запросе к API."

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "👋 Привет! Добро пожаловать в BIN Checker Bot!\n\n"
        "🔹 Этот бот позволяет проверять BIN банковских карт.\n"
        "🔹 Используй команду /bin <BIN> или !bin <BIN> для проверки карты.\n"
        "Пример: /bin 457173 или !bin 457173"
    )
    await message.answer(welcome_text)

@dp.message()
async def bin_message_handler(message: types.Message):
    text = message.text or ""
    text = text.strip()
    if text.startswith("/bin"):
        args = text[4:].strip()
    elif text.startswith("!bin"):
        args = text[4:].strip()
    else:
        return  # Игнорируем все остальные сообщения

    if not args:
        await message.answer("❌ Укажи BIN после команды, например: /bin 457173 или !bin 457173")
        return
    bin_number = args.strip()
    if not bin_number.isdigit() or len(bin_number) < 6:
        await message.answer("❌ Введи корректный BIN — минимум 6 цифр.")
        return
    response = bin_lookup(bin_number[:6])
    await message.answer(response)

# ================== RUN BOT ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
