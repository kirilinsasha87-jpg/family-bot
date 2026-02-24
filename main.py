import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram import F

TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
ADMIN_CHAT_ID = -100XXXXXXXXX  # id админ группы
MAIN_GROUP_ID = -100XXXXXXXXX  # id основной группы

bot = Bot(TOKEN)
dp = Dispatcher()

db = sqlite3.connect("database.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS approved_users(
user_id INTEGER PRIMARY KEY
)
""")
db.commit()

user_data = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Здравствуйте! Заполните анкету.\nВведите ваш ник:")
    user_data[message.from_user.id] = {}

@dp.message()
async def form_handler(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        return
    
    data = user_data[user_id]
    
    if "nick" not in data:
        data["nick"] = message.text
        await message.answer("Текущий LVL:")
    elif "lvl" not in data:
        data["lvl"] = message.text
        await message.answer("Лицензии:")
    elif "lic" not in data:
        data["lic"] = message.text
        await message.answer("Права на авто (+/-):")
    elif "auto" not in data:
        data["auto"] = message.text
        await message.answer("Права на оружие (+/-):")
    elif "weapon" not in data:
        data["weapon"] = message.text
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
            ]
        ])
        
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"Новая заявка:\n\n"
            f"Ник: {data['nick']}\n"
            f"LVL: {data['lvl']}\n"
            f"Лицензии: {data['lic']}\n"
            f"Авто: {data['auto']}\n"
            f"Оружие: {data['weapon']}",
            reply_markup=kb
        )
        
        await message.answer("Ваша заявка отправлена. Ожидайте решения.")
        del user_data[user_id]

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    cursor.execute("INSERT OR IGNORE INTO approved_users VALUES (?)", (user_id,))
    db.commit()
    
    invite_link = await bot.create_chat_invite_link(MAIN_GROUP_ID, member_limit=1)
    await bot.send_message(user_id, f"Ваша заявка одобрена!\nСсылка: {invite_link.invite_link}")
    await callback.answer("Одобрено")

@dp.chat_member()
async def check_member(event: types.ChatMemberUpdated):
    if event.chat.id == MAIN_GROUP_ID:
        user_id = event.from_user.id
        cursor.execute("SELECT user_id FROM approved_users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if not result:
            await bot.ban_chat_member(MAIN_GROUP_ID, user_id)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
