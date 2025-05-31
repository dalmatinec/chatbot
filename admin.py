# admin.py
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, RESTRICTED, LEFT, MEMBER
from aiogram.enums import ChatType
from config import DB_PATH, ALLOWED_CHAT_ID, BOT_TOKEN, OWNERS, ADMINS
from database import Database
import logging

router = Router()
db = Database(DB_PATH)
bot = Bot(token=BOT_TOKEN)

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

# Получение ID пользователя
@router.message(Command("getid"))
async def get_id(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    user_id = message.reply_to_message.from_user.id
    username = message.reply_to_message.from_user.username or "Без юзернейма"
    await message.answer(f"🦁 ID: {user_id} | Юзернейм: @{username}", parse_mode="HTML")
    logging.info(f"🦁 **Команда /getid** для user_id={user_id}, username={username}")

# Команды для прав на рассылку
@router.message(Command("open"))
async def open_forward(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    user_id = None
    full_name = None
    username = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        full_name = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.full_name}</a>"
        username = message.reply_to_message.from_user.username or f"ID {user_id}"
        db.add_user(user_id, f"@{username}")
    else:
        try:
            target = message.text.split(maxsplit=1)[1].strip()
            if target.startswith("@"):
                username = target[1:]
                user_id = db.get_user_id_by_username(username)
                if user_id:
                    try:
                        user = await bot.get_chat_member(message.chat.id, user_id)
                        full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                        db.add_user(user_id, f"@{user.user.username or f'ID {user_id}'}")
                    except Exception as e:
                        logging.error(f"Ошибка получения пользователя {target} через API: {e}", exc_info=True)
                        full_name = target
                else:
                    # Попробуем найти через API Telegram
                    try:
                        # Ищем пользователя по username через чат
                        members = await bot.get_chat_administrators(message.chat.id)
                        for member in members:
                            if member.user.username and member.user.username.lower() == username.lower():
                                user_id = member.user.id
                                full_name = f"<a href='tg://user?id={user_id}'>{member.user.full_name}</a>"
                                db.add_user(user_id, f"@{member.user.username}")
                                break
                        if not user_id:
                            # Если не админ, пробуем через get_chat_member
                            chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
                            user_id = chat_member.user.id
                            full_name = f"<a href='tg://user?id={user_id}'>{chat_member.user.full_name}</a>"
                            db.add_user(user_id, f"@{chat_member.user.username or f'ID {user_id}'}")
                    except Exception as e:
                        logging.error(f"Ошибка поиска пользователя {target}: {e}", exc_info=True)
                        await message.answer(f"❌ Пользователь {target} не найден!", parse_mode="HTML")
                        return
            else:
                user_id = int(target)
                try:
                    user = await bot.get_chat_member(message.chat.id, user_id)
                    full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                    username = user.user.username or f"ID {user_id}"
                    db.add_user(user_id, f"@{username}")
                except Exception as e:
                    logging.error(f"Ошибка получения пользователя ID {user_id}: {e}", exc_info=True)
                    await message.answer(f"❌ Пользователь ID {target} не найден!", parse_mode="HTML")
                    return
        except (IndexError, ValueError):
            await message.answer("❌ Укажите пользователя через реплай, ID или юзернейм!", parse_mode="HTML")
            return
    try:
        db.add_forward_permission(message.chat.id, user_id)
        await message.answer(
            f"✅ Готово! Теперь {full_name} в списке доверенных\n"
            f"📬 Добро пожаловать в клуб спамеров!",
            parse_mode="HTML"
        )
        logging.info(f"🔓 **Права выданы** пользователю {user_id} (username={username}) в чате {message.chat.id}")
    except Exception as e:
        logging.error(f"Ошибка добавления прав для user_id={user_id}: {e}", exc_info=True)
        await message.answer(f"❌ Не удалось выдать права! Ошибка: {str(e)}", parse_mode="HTML")

@router.message(Command("close"))
async def close_forward(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    user_id = None
    full_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        full_name = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.full_name}</a>"
    else:
        try:
            target = message.text.split(maxsplit=1)[1].strip()
            if target.startswith("@"):
                user_id = db.get_user_id_by_username(target[1:])
                if user_id:
                    try:
                        user = await bot.get_chat_member(message.chat.id, user_id)
                        full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                    except:
                        full_name = target
                else:
                    await message.answer(f"❌ Пользователь {target} не найден!", parse_mode="HTML")
                    return
            else:
                user_id = int(target)
                try:
                    user = await bot.get_chat_member(message.chat.id, user_id)
                    full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                except:
                    full_name = f"ID {user_id}"
        except (IndexError, ValueError):
            await message.answer("❌ Укажите пользователя через реплай, ID или юзернейм!", parse_mode="HTML")
            return
    db.remove_forward_permission(message.chat.id, user_id)
    await message.answer(
        f"🚫 Права на рассылку отозваны у {full_name}!\n"
        f"📩 Для разблокировки — обратись к админам.",
        parse_mode="HTML"
    )
    logging.info(f"🔒 **Права забраны** у пользователя {user_id} в чате {message.chat.id}")

# Команды для бана
@router.message(Command("ban"))
async def ban_user(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    user_id = None
    full_name = None
    username = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        full_name = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.full_name}</a>"
        username = message.reply_to_message.from_user.username or f"ID {user_id}"
        db.add_user(user_id, f"@{username}")
    else:
        try:
            target = message.text.split(maxsplit=1)[1].strip()
            if target.startswith("@"):
                user_id = db.get_user_id_by_username(target[1:])
                if user_id:
                    try:
                        user = await bot.get_chat_member(message.chat.id, user_id)
                        full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                        username = user.user.username or f"ID {user_id}"
                        db.add_user(user_id, f"@{username}")
                    except Exception as e:
                        logging.error(f"Ошибка получения пользователя {target}: {e}", exc_info=True)
                        full_name = target
                        username = target[1:]
                else:
                    await message.answer(f"❌ Пользователь {target} не найден!", parse_mode="HTML")
                    logging.warning(f"Пользователь {target} не найден в базе")
                    return
            else:
                user_id = int(target)
                try:
                    user = await bot.get_chat_member(message.chat.id, user_id)
                    full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                    username = user.user.username or f"ID {user_id}"
                    db.add_user(user_id, f"@{username}")
                except Exception as e:
                    logging.error(f"Ошибка получения пользователя ID {user_id}: {e}", exc_info=True)
                    await message.answer(f"❌ Пользователь ID {target} не найден!", parse_mode="HTML")
                    return
        except (IndexError, ValueError):
            await message.answer("❌ Укажите пользователя через реплай, ID или юзернейм!", parse_mode="HTML")
            return
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
        db.add_ban(message.chat.id, user_id)
        await message.answer(
            f"🚷 БАНхаммер активирован для {full_name}!\n"
            f"🔕 Покой и тишина восстановлены.",
            parse_mode="HTML"
        )
        logging.info(f"🚫 **Пользователь {user_id} (username={username}) забанен** в чате {message.chat.id}")
    except Exception as e:
        logging.error(f"Ошибка бана пользователя {user_id}: {e}", exc_info=True)
        await message.answer(f"❌ Не удалось забанить пользователя! Ошибка: {str(e)}", parse_mode="HTML")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    user_id = None
    full_name = None
    username = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        full_name = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.full_name}</a>"
        username = message.reply_to_message.from_user.username or f"ID {user_id}"
        db.add_user(user_id, f"@{username}")
    else:
        try:
            target = message.text.split(maxsplit=1)[1].strip()
            if target.startswith("@"):
                user_id = db.get_user_id_by_username(target[1:])
                if user_id:
                    try:
                        user = await bot.get_chat_member(message.chat.id, user_id)
                        full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                        username = user.user.username or f"ID {user_id}"
                        db.add_user(user_id, f"@{username}")
                    except Exception as e:
                        logging.error(f"Ошибка получения пользователя {target}: {e}", exc_info=True)
                        full_name = target
                        username = target[1:]
                else:
                    await message.answer(f"❌ Пользователь {target} не найден!", parse_mode="HTML")
                    logging.warning(f"Пользователь {target} не найден в базе")
                    return
            else:
                user_id = int(target)
                try:
                    user = await bot.get_chat_member(message.chat.id, user_id)
                    full_name = f"<a href='tg://user?id={user_id}'>{user.user.full_name}</a>"
                    username = user.user.username or f"ID {user_id}"
                    db.add_user(user_id, f"@{username}")
                except Exception as e:
                    logging.error(f"Ошибка получения пользователя ID {user_id}: {e}", exc_info=True)
                    await message.answer(f"❌ Пользователь ID {target} не найден!", parse_mode="HTML")
                    return
        except (IndexError, ValueError):
            await message.answer("❌ Укажите пользователя через реплай, ID или юзернейм!", parse_mode="HTML")
            return
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
        db.remove_ban(message.chat.id, user_id)
        await message.answer(
            f"🧙‍♂️ Снято заклятие бана для {full_name}.\n"
            f"✅ Добро пожаловать обратно в чат!",
            parse_mode="HTML"
        )
        logging.info(f"✅ **Пользователь {user_id} (username={username}) разбанен** в чате {message.chat.id}")
    except Exception as e:
        logging.error(f"Ошибка разбана пользователя {user_id}: {e}", exc_info=True)
        await message.answer(f"❌ Не удалось разбанить пользователя! Ошибка: {str(e)}", parse_mode="HTML")

# Удаление форвардов без прав
@router.message(F.forward_date)
async def check_forward(message: Message):
    if not is_allowed_chat(message.chat.id):
        return
    if not db.check_forward_permission(message.chat.id, message.from_user.id):
        user_id = message.from_user.id
        full_name = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"
        await message.delete()
        await message.answer(
            f"{full_name}\n"
            f"😅 Упс! У тебя пока нет прав на рассылку.\n"
            f"✉️ Напиши админам — они помогут! /adm",
            parse_mode="HTML"
        )
        logging.info(f"🗑️ **Форвард удален** от {message.from_user.id} в чате {message.chat.id}")

# Удаление системных сообщений о банах
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | RESTRICTED | LEFT | MEMBER)))
async def delete_ban_message(event: ChatMemberUpdated):
    if event.new_chat_member.status in ["kicked"]:
        try:
            await bot.delete_message(chat_id=event.chat.id, message_id=event.message_id)
            logging.info(f"🗑️ **Системное сообщение о бане удалено** в чате {event.chat.id}")
        except Exception as e:
            logging.error(f"Ошибка удаления системного сообщения о бане: {e}", exc_info=True)
    elif event.new_chat_member.status == "member" and event.old_chat_member.status in ["kicked"]:
        try:
            await bot.delete_message(chat_id=event.chat.id, message_id=event.message_id)
            logging.info(f"🗑️ **Системное сообщение о разбане удалено** в чате {event.chat.id}")
        except Exception as e:
            logging.error(f"Ошибка удаления системного сообщения о разбане: {e}", exc_info=True)

# Команды для топ-магазинов
@router.message(Command("addtop"))
async def add_top_shop(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    if message.reply_to_message:
        username = message.reply_to_message.from_user.username
        if not username:
            await message.answer("❌ У пользователя нет username!", parse_mode="HTML")
            return
        db.add_top_shop(message.chat.id, f"@{username}", "")
        await message.answer(f"🏆 Магазин @{username} добавлен в топ!", parse_mode="HTML")
        logging.info(f"🏆 **Магазин @{username} добавлен** в топ в чате {message.chat.id}")
    else:
        try:
            username = message.text.split(maxsplit=1)[1].strip()
            db.add_top_shop(message.chat.id, username, "")
            await message.answer(f"🏆 Магазин {username} добавлен в топ!", parse_mode="HTML")
            logging.info(f"🏆 **Магазин {username} добавлен** в топ в чате {message.chat.id}")
        except IndexError:
            await message.answer("❌ Укажите username магазина!", parse_mode="HTML")

@router.message(Command("deltop"))
async def delete_top_shop(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    try:
        username = message.text.split(maxsplit=1)[1].strip()
        db.delete_top_shop(message.chat.id, username)
        await message.answer(f"🗑️ Магазин {username} удален из топа!", parse_mode="HTML")
        logging.info(f"🗑️ **Магазин {username} удален** из топа в чате {message.chat.id}")
    except IndexError:
        await message.answer("❌ Укажите username магазина!", parse_mode="HTML")

@router.message(Command("des"))
async def set_description(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        return
    if message.reply_to_message:
        description = message.reply_to_message.text
        try:
            username = message.text.split(maxsplit=1)[1].strip()
            db.add_top_shop(message.chat.id, username, description)
            await message.answer(f"📝 Описание для {username} обновлено!", parse_mode="HTML")
            logging.info(f"📝 **Описание обновлено** для {username} в чате {message.chat.id}")
        except IndexError:
            await message.answer("❌ Укажите username магазина!", parse_mode="HTML")
    else:
        await message.answer("❌ Ответьте на сообщение с описанием!", parse_mode="HTML")

@router.message(Command("top"))
async def show_top_shops(message: Message):
    if not is_allowed_chat(message.chat.id):
        await message.answer("🚫 Эта команда работает только в разрешенном чате!", parse_mode="HTML")
        return
    shops = db.get_top_shops(message.chat.id)
    if not shops:
        await message.answer("🏆 Список топ-магазинов пуст!", parse_mode="HTML")
        return
    text = "🏆 Топ магазины:\n"
    for i, (username, description) in enumerate(shops):
        text += f"▫️ {username}\n🗂 {description or 'Без описания'}\n"
        if i < len(shops) - 1:  # Добавляем разделитель только между магазинами
            text += "➖➖➖➖➖\n"
    await message.answer(text, parse_mode="HTML")
    logging.info(f"🏆 **Показан список топ-магазинов** в чате {message.chat.id}")

# Статистика триггеров (админская команда в ЛС)
@router.message(Command("stat"), F.chat.type.in_({ChatType.PRIVATE}))
async def show_trigger_stats(message: Message):
    user_id = message.from_user.id
    if user_id not in OWNERS and user_id not in ADMINS:
        await message.answer("🚫 Вы не администратор!", parse_mode="HTML")
        logging.warning(f"Пользователь {user_id} пытался вызвать /stat без прав")
        return
    stats = db.get_trigger_stats()
    if not stats:
        await message.answer("📊 Статистика триггеров пуста!", parse_mode="HTML")
        return
    text = "📊 Статистика триггеров:\n\n"
    for trigger_word, count in stats:
        text += f"▫️ {trigger_word}: {count} вызов(ов)\n"
    await message.answer(text, parse_mode="HTML")
    logging.info(f"📊 **Статистика триггеров показана** пользователю {user_id}")