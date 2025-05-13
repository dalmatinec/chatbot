# handlers.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters
from config import OWNER_ID
import database
import utils
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_chat_registered(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    # Владелец в ЛС может работать без регистрации чата
    if user_id == OWNER_ID and update.effective_chat.type == "private":
        return True
    # Для админов в ЛС проверяем последний зарегистрированный чат
    if update.effective_chat.type == "private":
        last_chat_id = database.get_owner_last_chat(user_id)
        if not last_chat_id:
            update.message.reply_text("Сначала зарегистрируйте чат через /newchat!")
            return False
        return True
    # В чате проверяем регистрацию
    if not database.is_chat_registered(chat_id):
        update.message.reply_text("Чат не подключен! Используйте /newchat для регистрации.")
        return False
    return True

def check_admin(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id == OWNER_ID:
        return True
    if update.effective_chat.type == "private":
        chat_id = database.get_owner_last_chat(user_id)
        if not chat_id:
            return False
    return database.is_admin(chat_id, user_id)

def help_command(update, context):
    if not check_chat_registered(update, context):
        return
    text = (
        "/help - Список команд\n"
        "/ban - Забанить пользователя\n"
        "/mute - Замутить пользователя\n"
        "/addtrigger - Добавить триггер (в ЛС бота)\n"
        "/deltrigger - Удалить триггер (в ЛС бота)\n"
        "/newchat - Перенос чата (владелец)\n"
        "/chatid - Показать ID чата\n"
        "/addadmin - Добавить админа\n"
        "/deladmin - Удалить админа\n"
        "/send - Дать права на пересылку\n"
        "/delsend - Убрать права на пересылку\n"
        "/vip - Добавить VIP\n"
        "/delvip - Удалить VIP\n"
        "/top - Показать топ участников\n"
        "/menu - Показать меню\n"
    )
    update.message.reply_text(text)

def ban_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    chat_id = update.effective_chat.id
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя!")
        return
    args = context.args
    duration = args[0] if args else None
    until_date = utils.parse_duration(duration) if duration else None
    context.bot.kick_chat_member(chat_id, user.id, until_date=until_date)
    update.message.reply_text(f"Пользователь @{user.username or user.id} забанен!")

def mute_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    chat_id = update.effective_chat.id
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя!")
        return
    args = context.args
    duration = args[0] if args else None
    until_date = utils.parse_duration(duration) if duration else None
    context.bot.restrict_chat_member(chat_id, user.id, until_date=until_date, permissions=utils.mute_permissions())
    update.message.reply_text(f"Пользователь @{user.username or user.id} замьючен!")

def add_trigger_command(update, context):
    user_id = update.effective_user.id
    logger.info(f"Попытка создать триггер: user_id={user_id}, chat_type={update.effective_chat.type}")
    if update.effective_chat.type != "private":
        update.message.reply_text("Триггеры создаются только в ЛС бота!")
        logger.info("Попытка создать триггер в чате, отклонено")
        return
    chat_id = database.get_owner_last_chat(user_id)
    if user_id != OWNER_ID and not chat_id:
        update.message.reply_text("Сначала зарегистрируйте чат через /newchat!")
        logger.info("Нет зарегистрированного чата для не-владельца")
        return
    if user_id != OWNER_ID and not database.is_admin(chat_id, user_id):
        update.message.reply_text("Только админы или владелец могут создавать триггеры!")
        logger.info("Пользователь не админ и не владелец")
        return
    if not update.message.reply_to_message:
        update.message.reply_text("Ответь на сообщение, которое станет ответом триггера!")
        logger.info("Нет ответа на сообщение")
        return
    args = context.args
    logger.info(f"Аргументы команды: {args}")
    if not args:
        update.message.reply_text("Укажи команду или слово триггера (например: /addtrigger /sort или /addtrigger Правила)!")
        logger.info("Аргументы отсутствуют")
        return
    trigger_text = args[0]
    # Если владелец и нет чата, создаём временный чат
    if user_id == OWNER_ID and not chat_id:
        chat_id = -1002608009207
        database.register_chat(chat_id)
        database.set_owner_last_chat(user_id, chat_id)
        logger.info(f"Создан временный чат {chat_id} для владельца")
    response_text = update.message.reply_to_message.text
    if not response_text:
        update.message.reply_text("Ответное сообщение не содержит текста!")
        logger.info("Ответное сообщение пустое")
        return
    database.add_trigger(chat_id, trigger_text, response_text)
    update.message.reply_text(f"Триггер {trigger_text} добавлен для чата {chat_id}!")
    logger.info(f"Триггер {trigger_text} успешно добавлен для чата {chat_id}")

def delete_trigger_command(update, context):
    user_id = update.effective_user.id
    if update.effective_chat.type != "private":
        update.message.reply_text("Триггеры удаляются только в ЛС бота!")
        return
    chat_id = database.get_owner_last_chat(user_id)
    if user_id != OWNER_ID and not chat_id:
        update.message.reply_text("Сначала зарегистрируйте чат через /newchat!")
        return
    if user_id != OWNER_ID and not database.is_admin(chat_id, user_id):
        update.message.reply_text("Только админы или владелец могут удалять триггеры!")
        return
    args = context.args
    if not args:
        update.message.reply_text("Укажи триггер для удаления (например: /deltrigger /sort или /deltrigger Правила)!")
        return
    trigger_text = args[0]
    if user_id == OWNER_ID and not chat_id:
        chat_id = -1002608009207
    database.delete_trigger(chat_id, trigger_text)
    update.message.reply_text(f"Триггер {trigger_text} удалён из чата {chat_id}!")

def new_chat_command(update, context):
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("Только владелец бота может переносить чат!")
        return
    args = context.args
    if not args:
        update.message.reply_text("Укажи ID нового чата!")
        return
    try:
        new_chat_id = int(args[0])
    except ValueError:
        update.message.reply_text("ID чата должен быть числом!")
        return
    old_chat_id = update.effective_chat.id if update.effective_chat.type != "private" else None
    database.register_chat(new_chat_id)
    database.set_owner_last_chat(update.effective_user.id, new_chat_id)
    if old_chat_id and database.is_chat_registered(old_chat_id):
        database.transfer_chat_data(old_chat_id, new_chat_id)
        update.message.reply_text(f"Чат перенесён на ID {new_chat_id}! Все настройки и триггеры перенесены. 🏴‍☠️")
    else:
        update.message.reply_text(f"Новый чат {new_chat_id} зарегистрирован! 🏴‍☠️")

def chat_id_command(update, context):
    if not check_chat_registered(update, context):
        return
    chat_id = update.effective_chat.id
    update.message.reply_text(f"ID чата: {chat_id}")

def add_admin_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя!")
        return
    database.add_admin(update.effective_chat.id, user.id)
    update.message.reply_text(f"Пользователь @{user.username or user.id} теперь админ!")

def delete_admin_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя!")
        return
    database.remove_admin(update.effective_chat.id, user.id)
    update.message.reply_text(f"Пользователь @{user.username or user.id} больше не админ!")

def add_send_permission_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя/бота/чата!")
        return
    database.add_send_permission(update.effective_chat.id, user.id)
    update.message.reply_text(f"Права на пересылку выданы @{user.username or user.id}!")

def delete_send_permission_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        update.message.reply_text("Ответь на сообщение пользователя/бота/чата!")
        return
    database.remove_send_permission(update.effective_chat.id, user.id)
    update.message.reply_text(f"Права на пересылку у @{user.username or user.id} отозваны!")

def add_vip_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    chat_id = update.effective_chat.id
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        args = context.args
        if not args:
            update.message.reply_text("Ответь на сообщение пользователя или укажи @username!")
        username = args[0].lstrip('@')
        user_id = username
    else:
        user_id = user.id
        username = user.username or str(user.id)
    database.add_vip(chat_id, user_id, username)
    update.message.reply_text(f"Пользователь @{username} добавлен в VIP!")

def delete_vip_command(update, context):
    if not check_chat_registered(update, context) or not check_admin(update, context):
        return
    chat_id = update.effective_chat.id
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        args = context.args
        if not args:
            update.message.reply_text("Ответь на сообщение пользователя или укажи @username!")
            return
        username = args[0].lstrip('@')
        user_id = username
    else:
        user_id = user.id
        username = user.username or str(user.id)
    database.remove_vip(chat_id, user_id)
    update.message.reply_text(f"Пользователь @{username} удалён из VIP!")

def top_command(update, context):
    if not check_chat_registered(update, context):
        return
    vips = database.get_vips(update.effective_chat.id)
    if not vips:
        update.message.reply_text("Список VIP пуст!")
        return
    text = "Топ участников:\n" + "\n".join([f"@{vip[1]}" for vip in vips])
    update.message.reply_text(text)

def menu_command(update, context):
    if not check_chat_registered(update, context):
        return
    username = update.effective_user.username or update.effective_user.first_name
    text = (
        f"{username}\nДобро пожаловать!\n\n"
        "⚠️ Только органические товары! ♻️\n"
        "         🔞 Строго 18+!\n\n"
        "Выберите и нажмите кнопку👇"
    )
    keyboard = [
        [InlineKeyboardButton("Сорт 🌳", callback_data="sort"),
         InlineKeyboardButton("Дус | Сд 🌲", callback_data="sd")],
        [InlineKeyboardButton("Гаш 🌑", callback_data="hash"),
         InlineKeyboardButton("Первак | Центр 🍂", callback_data="centr")],
        [InlineKeyboardButton("Шала | Трим 🍃", callback_data="shala"),
         InlineKeyboardButton("Вакс 🍯", callback_data="wax")],
        [InlineKeyboardButton("Грибы 🍄", callback_data="mushrooms"),
         InlineKeyboardButton("КаннаФуд 🍫", callback_data="cannafood")],
        [InlineKeyboardButton("Бот Быстрых покупок ⚡️", url="http://t.me/PiratesFastbot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text, reply_markup=reply_markup)

def button_callback(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    trigger_text = f"/{query.data}"
    response = database.get_trigger_response(chat_id, trigger_text)
    if response:
        query.message.reply_text(response)
    query.answer()

def sort_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/sort")
    if response:
        update.message.reply_text(response)

def hash_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/hash")
    if response:
        update.message.reply_text(response)

def dus_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/dus")
    if response:
        update.message.reply_text(response)

def sd_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/sd")
    if response:
        update.message.reply_text(response)

def centr_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/centr")
    if response:
        update.message.reply_text(response)

def pervak_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/pervak")
    if response:
        update.message.reply_text(response)

def shala_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/shala")
    if response:
        update.message.reply_text(response)

def trim_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/trim")
    if response:
        update.message.reply_text(response)

def wax_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/wax")
    if response:
        update.message.reply_text(response)

def mushrooms_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/mushrooms")
    if response:
        update.message.reply_text(response)

def cannafood_command(update, context):
    if not check_chat_registered(update, context):
        return
    response = database.get_trigger_response(update.effective_chat.id, "/cannafood")
    if response:
        update.message.reply_text(response)

def handle_message(update, context):
    chat_id = update.effective_chat.id
    if not database.is_chat_registered(chat_id):
        return
    message = update.message
    # Проверка пересылок
    if (message.forward_from or 
        message.forward_from_chat or 
        message.forward_from_message_id or 
        message.forward_sender_name):
        source_id = (
            message.forward_from.id if message.forward_from else
            message.forward_from_chat.id if message.forward_from_chat else
            message.from_user.id if message.from_user else
            0  # Для анонимных пересылок
        )
        logger.info(f"Проверка пересылки: source_id={source_id}, chat_id={chat_id}")
        if source_id == 0 or not database.has_send_permission(chat_id, source_id):
            try:
                context.bot.delete_message(chat_id, message.message_id)
                context.bot.send_message(
                    chat_id,
                    f"@{message.from_user.username or message.from_user.id if message.from_user else 'Аноним'}, "
                    "у вас нет прав на пересылку! Обратитесь к админу для получения прав."
                )
                logger.info(f"Пересылка от {source_id} удалена в чате {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения: {e}")
            return
    # Проверка триггеров
    text = message.text.lower() if message.text else ""
    response = database.get_trigger_response(chat_id, text)
    if response:
        update.message.reply_text(response)
