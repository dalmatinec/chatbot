# main.py
import config  # Добавляем импорт
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from handlers import *
import database

def main():
    updater = Updater(config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Инициализация базы
    database.init_db()

    # Команды
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("ban", ban_command))
    dp.add_handler(CommandHandler("mute", mute_command))
    dp.add_handler(CommandHandler("addtrigger", add_trigger_command))
    dp.add_handler(CommandHandler("deltrigger", delete_trigger_command))
    dp.add_handler(CommandHandler("newchat", new_chat_command))
    dp.add_handler(CommandHandler("chatid", chat_id_command))
    dp.add_handler(CommandHandler("addadmin", add_admin_command))
    dp.add_handler(CommandHandler("deladmin", delete_admin_command))
    dp.add_handler(CommandHandler("send", add_send_permission_command))
    dp.add_handler(CommandHandler("delsend", delete_send_permission_command))
    dp.add_handler(CommandHandler("vip", add_vip_command))
    dp.add_handler(CommandHandler("delvip", delete_vip_command))
    dp.add_handler(CommandHandler("top", top_command))
    dp.add_handler(CommandHandler("menu", menu_command))
    dp.add_handler(CommandHandler("sort", sort_command))
    dp.add_handler(CommandHandler("hash", hash_command))
    dp.add_handler(CommandHandler("dus", dus_command))
    dp.add_handler(CommandHandler("sd", sd_command))
    dp.add_handler(CommandHandler("centr", centr_command))
    dp.add_handler(CommandHandler("pervak", pervak_command))
    dp.add_handler(CommandHandler("shala", shala_command))
    dp.add_handler(CommandHandler("trim", trim_command))
    dp.add_handler(CommandHandler("wax", wax_command))
    dp.add_handler(CommandHandler("mushrooms", mushrooms_command))
    dp.add_handler(CommandHandler("cannafood", cannafood_command))

    # Обработчик сообщений и пересылок
    dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))

    # Обработчик кнопок
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Старт бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
