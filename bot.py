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
def bin_lookup(full_number: str) -> str:
    """Берёт первые 6 цифр карты для запроса к Binlist API"""
    digits = ''.join(c for c in full_number if c.isdigit())
    if len(digits) < 6:
        return "❌ Введи корректный BIN — минимум 6 цифр."
    bin_number = digits[:6]
    
    url = f"https://lookup.binlist.net/{bin_number}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return "❌ BIN не найден или недействителен."
        data = r.json()
        country_code = data.get('country', {}).get('alpha2', '')
        flag = country_flag(country_code)
        # Красивый дизайн ответа
        return (
            f"💳 **BIN:** `{bin_number}`\n"
            f"🏦 **Банк:** {data.get('bank', {}).get('name', 'N/A')}\n"
            f"🌍 **Страна:** {flag}\n"
            f"💼 **Тип:** {data.get('type', 'N/A')}\n"
            f"💳 **Система:** {data.get('scheme', 'N/A')}\n"
            f"🏷 **Бренд:** {data.get('brand', 'N/A')}"
        )
    except Exception:
        return "⚠️ Ошибка при запросе к API."

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "👋 Привет! Добро пожаловать в BIN Checker Bot!\n\n"
        "🔹 Этот бот позволяет проверять BIN банковских карт.\n"
        "🔹 Используй команду /bin <номер карты> или !bin <номер карты> для проверки.\n"
        "Пример: /bin 4165985824414481 или !bin 457173XXXXXX"
    )
    await message.answer(welcome_text)

@dp.message()
async def bin_message_handler(message: types.Message):
    text = (message.text or "").strip()
    
    if text.startswith("/bin"):
        args = text[4:].strip()
    elif text.startswith("!bin"):
        args = text[4:].strip()
    else:
        return  # Игнорируем все остальные сообщения

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
