import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import csv

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

# ================== DATABASE ==================
DB_PATH = "bins.db"

def init_db(csv_file="ranges.csv"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bins (
            bin TEXT PRIMARY KEY,
            bank TEXT,
            type TEXT,
            scheme TEXT,
            brand TEXT,
            country TEXT
        )
    """)
    conn.commit()

    # Импорт CSV в базу
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT OR REPLACE INTO bins VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row.get("bin", ""),
                    row.get("bank_name", "N/A"),
                    row.get("type", "N/A"),
                    row.get("scheme", "N/A"),
                    row.get("brand", "N/A"),
                    row.get("country_code", "")
                ))
        conn.commit()
    conn.close()

def get_from_db(bin_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bins WHERE bin=?", (bin_number[:6],))
    row = cursor.fetchone()
    conn.close()
    return row

# ================== COUNTRY FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== BIN CHECKER ==================
BIN_CACHE = {}

def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())
    if len(bin_number) < 6:
        return "❌ Введи корректный BIN — минимум 6 цифр."
    bin_number = bin_number[:6]

    # Проверяем кэш
    if bin_number in BIN_CACHE:
        return BIN_CACHE[bin_number]

    # Проверяем базу
    row = get_from_db(bin_number)
    if row:
        _, bank, type_, scheme, brand, country = row
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

    return "❌ BIN не найден в базе."

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в локальный BIN Checker Bot!\n\n"
        "🔹 Используй команду /bin <номер карты> или !bin <номер карты> для проверки.\n"
        "Пример: /bin 416598XXXXXX или !bin 457173XXXXXX"
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
    init_db()  # инициализация базы из CSV
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
