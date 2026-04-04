import asyncio
import logging
import os
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from mimesis import Person, Address

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = "PUB-0YLp2Jn3Qbw7qlY4Gu1gPMSR4"

# 🔒 ДОСТУП
ALLOWED_USERS = {1003539611,7979473115,8270778815,7215287573}
ALLOWED_CHATS = {-1003392192892}

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

    response = (
        f"<b>Info ⇾</b> <code>{scheme} - {type_} - {brand}</code>\n"
        f"<b>Issuer ⇾</b> <code>{bank}</code>\n"
        f"<b>Country ⇾</b> <code>{country_name}</code> {flag}"
    )

    BIN_CACHE[bin_number] = response
    return response

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 MoonBIN Bot\n\n"
        "Команды:\n"
        "/bin 457173\n"
        "!bin 457173\n\n"
        "/fake us\n"
        "/fake ru\n"
        "/fake sr"
    )

@dp.message()
async def bin_handler(message: types.Message):
    user_id = message.from_user.id

    # 🔒 ЛС
    if message.chat.type == "private":
        if user_id not in ALLOWED_USERS:
            return

    # 🔒 ЧАТЫ
    if message.chat.type in ["group", "supergroup"]:
        if message.chat.id not in ALLOWED_CHATS:
            return

    text = (message.text or "").strip()

    # ================== FAKE ==================
    if text.startswith("/fake") or text.startswith("!fake"):
        args = text.split()

        locale = "en"
        if len(args) > 1:
            locale = args[1].lower()

        try:
            person = Person(locale)
            address = Address(locale)
        except:
            await message.answer("❌ Неподдерживаемая страна")
            return

        name = person.full_name()
        street = f"{address.street_name()} {address.street_number()}"
        city = address.city()
        state = address.state()
        zip_code = address.postal_code()
        country = address.country()
        email = person.email()
        phone = person.telephone()

        response = (
            f"<b>MoonBIN</b>\n"
            f"<i>Fake Generator [{locale.upper()}]</i>\n\n"
            f"<b>Name ⇾</b> <code>{name}</code>\n\n"
            f"<b>Street ⇾</b> <code>{street}</code>\n"
            f"<b>City ⇾</b> <code>{city}</code>\n"
            f"<b>State ⇾</b> <code>{state}</code>\n"
            f"<b>ZIP ⇾</b> <code>{zip_code}</code>\n"
            f"<b>Country ⇾</b> <code>{country}</code>\n\n"
            f"<b>Email ⇾</b> <code>{email}</code>\n"
            f"<b>Phone ⇾</b> <code>{phone}</code>"
        )

        await message.answer(response, parse_mode="HTML")
        return

    # ================== BIN ==================
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

    await message.answer(response, parse_mode="HTML")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
