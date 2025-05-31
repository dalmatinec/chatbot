# triggers.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import DB_PATH, ALLOWED_CHAT_ID, OWNERS, ADMINS
from database import Database
import logging

router = Router()
db = Database(DB_PATH)

# Проверка, является ли пользователь админом или владельцем
async def is_admin(bot, chat_id, user_id):
    logging.info(f"Проверка is_admin: user_id={user_id}, chat_id={chat_id}")
    if user_id in OWNERS:
        logging.info(f"Пользователь {user_id} в OWNERS")
        return True
    if user_id in ADMINS:
        logging.info(f"Пользователь {user_id} в ADMINS")
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.is_chat_admin()
        logging.info(f"Проверка через API: user_id={user_id}, is_admin={is_admin}")
        return is_admin
    except Exception as e:
        logging.error(f"Ошибка проверки админа для user_id={user_id}: {e}")
        return False

# Проверка, является ли чат разрешенным
def is_allowed_chat(chat_id):
    return str(chat_id) == ALLOWED_CHAT_ID

@router.message(Command("addt"))
async def add_trigger(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение с текстом триггера!", parse_mode="HTML")
        return
    try:
        trigger_word = message.text.split()[1]
        response = message.reply_to_message.text
        db.add_trigger(message.chat.id, trigger_word, response)
        await message.answer(f"🛠️ Триггер '{trigger_word}' добавлен!", parse_mode="HTML")
        logging.info(f"🛠️ **Триггер {trigger_word} добавлен** в чате {message.chat.id}")
    except IndexError:
        await message.answer("❌ Укажите слово триггера!", parse_mode="HTML")

@router.message(Command("delt"))
async def delete_trigger(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    try:
        trigger_word = message.text.split()[1]
        db.delete_trigger(message.chat.id, trigger_word)
        await message.answer(f"🗑️ Триггер '{trigger_word}' удален!", parse_mode="HTML")
        logging.info(f"🗑️ **Триггер {trigger_word} удален** в чате {message.chat.id}")
    except IndexError:
        await message.answer("❌ Укажите слово триггера!", parse_mode="HTML")

@router.message(Command("triggers"))
async def list_triggers(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    triggers = db.get_triggers(message.chat.id)
    if not triggers:
        await message.answer("📋 Список триггеров пуст!", parse_mode="HTML")
        return
    text = "📋 Список триггеров:\n\n"
    for trigger_word, _ in triggers:
        text += f"▫️ {trigger_word}\n"
    await message.answer(text, parse_mode="HTML")
    logging.info(f"📋 **Показан список триггеров** в чате {message.chat.id}")

@router.message()
async def check_trigger(message: Message):
    if not is_allowed_chat(message.chat.id):
        return
    triggers = db.get_triggers(message.chat.id)
    for trigger_word, response in triggers:
        if trigger_word.lower() in message.text.lower():
            full_name = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>"
            response = response.replace("{full_name}", full_name)
            await message.answer(f"{response}", parse_mode="HTML")
            db.increment_trigger_stat(trigger_word)
            logging.info(f"🚀 **Триггер {trigger_word} сработал** в чате {message.chat.id}")
            break