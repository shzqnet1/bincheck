import asyncio
import logging
import os
import aiohttp
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from faker import Faker

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = "PUB-0YLp2Jn3Qbw7qlY4Gu1gPMSR4"

ALLOWED_USERS = {123456789}
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

# ================== FAKE ==================
async def fake_generator(country: str) -> str:
    country = country.lower()

    aliases = {
        "us": "usa", "ua": "ukraine", "ru": "russia",
        "de": "germany", "fr": "france", "es": "spain", "it": "italy"
    }

    country = aliases.get(country, country)

    locales = {
        "uk": "en_GB", "ireland": "en_IE", "france": "fr_FR",
        "germany": "de_DE", "spain": "es_ES", "italy": "it_IT",
        "netherlands": "nl_NL", "belgium": "nl_BE", "switzerland": "de_CH",
        "austria": "de_AT", "poland": "pl_PL", "czech": "cs_CZ",
        "slovakia": "sk_SK", "hungary": "hu_HU", "romania": "ro_RO",
        "bulgaria": "bg_BG", "greece": "el_GR", "portugal": "pt_PT",
        "sweden": "sv_SE", "norway": "no_NO", "finland": "fi_FI",
        "denmark": "da_DK", "estonia": "et_EE", "latvia": "lv_LV",
        "lithuania": "lt_LT", "ukraine": "uk_UA", "russia": "ru_RU",

        "usa": "en_US", "canada": "en_CA", "mexico": "es_MX",
        "brazil": "pt_BR", "argentina": "es_AR", "chile": "es_CL",
        "colombia": "es_CO", "peru": "es_PE", "venezuela": "es_VE",

        "china": "zh_CN", "japan": "ja_JP", "korea": "ko_KR",
        "india": "en_IN", "indonesia": "id_ID", "thailand": "th_TH",
        "vietnam": "vi_VN", "philippines": "en_PH", "malaysia": "ms_MY",
        "singapore": "en_SG",

        "turkey": "tr_TR", "uae": "en_AE", "saudi": "ar_SA",
        "israel": "he_IL",

        "southafrica": "en_ZA", "egypt": "ar_EG", "nigeria": "en_NG",
        "kenya": "en_KE", "morocco": "fr_MA",

        "australia": "en_AU", "newzealand": "en_NZ"
    }

    locale = locales.get(country, "en_US")
    fake = Faker(locale)

    name = fake.name()
    address = fake.address().replace("\n", ", ")
    email = fake.email()
    phone = fake.phone_number()

    return (
        f"<b>Fake Generator</b>\n\n"
        f"<b>Name ⇾</b> <code>{name}</code>\n"
        f"<b>Address ⇾</b> <code>{address}</code>\n"
        f"<b>Email ⇾</b> <code>{email}</code>\n"
        f"<b>Phone ⇾</b> <code>{phone}</code>"
    )

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

# ================== BIN ==================
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
        "👋 BIN Checker Bot\n\n"
        "Используй:\n/bin 457173\n!fake usa"
    )

@dp.message()
async def handler(message: types.Message):
    user_id = message.from_user.id

    if message.chat.type == "private":
        if user_id not in ALLOWED_USERS:
            return

    if message.chat.type in ["group", "supergroup"]:
        if message.chat.id not in ALLOWED_CHATS:
            return

    text = (message.text or "").strip()

    # 🔥 FAKE
    if text.startswith("!fake"):
        args = text[5:].strip()

        if not args:
            await message.answer("❌ Example: !fake usa")
            return

        response = await fake_generator(args)
        await message.answer(response, parse_mode="HTML")
        return

    # 🔥 BIN
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
