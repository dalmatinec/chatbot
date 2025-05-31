# handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatType
from config import DB_PATH, CATALOG_BOT, LINKS_CHANNEL, EXPRESS_BOT
from database import Database
import logging

router = Router()
db = Database(DB_PATH)

@router.message(CommandStart(), F.chat.type.in_({ChatType.PRIVATE}))
async def start_command(message: Message):
    user = message.from_user
    full_name = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    text = (
        f"<b>🏴‍☠️ Добро пожаловать, {full_name}! 🏴‍☠️\n\n"
        "📋 Ссылки, каталог магазинов и тех. поддержка вы сможете найти в нашем боте по кнопке ниже\n\n"
        "🛒 Я предоставляю витрину магазинов в чате 'Витрина' в переходнике\n\n"
        "⚠️ Прошу ознакомиться с правилами покупок и формой подачи жалоб\n"
        "Так как это может уберечь ваши средства от скама 🚨\n\n"
        "🚀 По кнопке ЭкспрессБот вы сможете сделать заказ, указав бюджет, желаемый район или заказать доставку, не отписывая всем операторам.\n\n"
        "🤝 Приятных сделок! 🏴‍☠️</b>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Бот каталог", url=f"https://t.me/{CATALOG_BOT[1:]}"),
            InlineKeyboardButton(text="🔗 Наши ссылки", url=f"https://t.me/{LINKS_CHANNEL[1:]}")
        ],
        [InlineKeyboardButton(text="🚀 Экспресс покупки", url=f"https://t.me/{EXPRESS_BOT[1:]}")]
    ])
    
    try:
        photo = FSInputFile("start.jpg")
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    logging.info(f"🚀 **Команда /start выполнена** пользователем {user.id}")

@router.message(Command("chatid"))
async def chat_id_command(message: Message):
    chat_id = message.chat.id
    await message.answer(f"🆔 ID чата: {chat_id}", parse_mode="HTML")
    logging.info(f"🆔 **Команда /chatid** в чате {chat_id}")

@router.message(Command("help"))
async def help_command(message: Message):
    text = (
        "📚 Список команд:\n"
        "🆔 /chatid - Показать ID чата\n"
        "📚 /help - Показать список команд\n"
        "🔓 /open - Выдать права на рассылку\n"
        "🔒 /close - Забрать права на рассылку\n"
        "🚫 /ban - Забанить пользователя\n"
        "✅ /unban - Разбанить пользователя\n"
        "🛠️ /addt - Добавить триггер\n"
        "🗑️ /delt - Удалить триггер\n"
        "📋 /triggers - Показать триггеры\n"
        "🏆 /addtop - Добавить магазин в топ\n"
        "🗑️ /deltop - Удалить магазин из топа\n"
        "📝 /des - Добавить описание магазина\n"
        "🆔 /getid - Показать ID пользователя\n"
        "🏆 /top - Показать топ-магазины\n"
        "📊 /stat - Показать статистику триггеров (админам в ЛС)"
    )
    await message.answer(text, parse_mode="HTML")
    logging.info(f"📚 **Команда /help** выполнена пользователем {message.from_user.id}")