import asyncio
import logging
import os
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = "PUB-0YLp2Jn3Qbw7qlY4Gu1gPMSR4"

# 🔒 ДОСТУП
ALLOWED_USERS = {123456789}  # свои ID
ALLOWED_CHATS = {-1003392192892}  # свой чат

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== CACHE ==================
BIN_CACHE = {}

# ================== FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== API ==================
async def fetch_bin(bin_number: str):
    url = f"https://data.handyapi.com/bin/{bin_number}"
    headers = {"x-api-key": API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            try:
                return await resp.json()
            except:
                return None

# ================== BIN CHECK ==================
async def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())

    if len(bin_number) < 6:
        return "❌ Введи минимум 6 цифр."

    bin_number = bin_number[:8]

    if bin_number in BIN_CACHE:
        return BIN_CACHE[bin_number]

    data = await fetch_bin(bin_number)

    if not data:
        return "❌ API не отвечает."

    if data.get("Status") != "SUCCESS":
        return f"❌ Ошибка API: {data}"

    bank = data.get("Issuer", "N/A")
    type_ = data.get("Type", "N/A")
    scheme = data.get("Scheme", "N/A")
    brand = data.get("CardTier", "N/A")

    country_code = data.get("Country", {}).get("A2", "")
    country_name = data.get("Country", {}).get("Name", "N/A")

    flag = country_flag(country_code)

    # 🔥 ДИЗАЙН КАК НА СКРИНЕ
    response = (
        f"<b>MOONBIN</b>\n\n"
        f"BIN      ➜ <code>{bin_number}</code>\n"
        f"COUNTRY  ➜ {flag} <code>{country_name}</code>\n"
        f"BANK     ➜ <code>{bank}</code>\n"
        f"BRAND    ➜ <code>{scheme}</code>\n"
        f"TYPE     ➜ <code>{type_}</code>"
    )

    BIN_CACHE[bin_number] = response
    return response

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 BIN Checker Bot\n\n"
        "Используй:\n/bin 457173\nили\n!bin 457173"
    )

@dp.message()
async def bin_handler(message: types.Message):
    user_id = message.from_user.id

    # 🔒 ЛС — только для разрешённых
    if message.chat.type == "private":
        if user_id not in ALLOWED_USERS:
            return

    # 🔒 ЧАТЫ — только разрешённые
    if message.chat.type in ["group", "supergroup"]:
        if message.chat.id not in ALLOWED_CHATS:
            return

    text = (message.text or "").strip()

    if text.startswith("/bin"):
        args = text[4:].strip()
    elif text.startswith("!bin"):
        args = text[4:].strip()
    else:
        return

    if not args:
        await message.answer("❌ Пример: /bin 457173")
        return

    response = await bin_lookup(args)

    # 🔥 SENT BY
    user = message.from_user
    username = f"@{user.username}" if user.username else user.full_name

    response += f"\nSENT BY ➜ {username}"

    await message.answer(response, parse_mode="HTML")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
