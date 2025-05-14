# main.py
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
import config
import handlers
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('bot.log'),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

def main():
    updater = Updater(config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", handlers.start_command, Filters.chat_type.private))
    dp.add_handler(CommandHandler("help", handlers.help_command))
    dp.add_handler(CommandHandler("ban", handlers.ban_command))
    dp.add_handler(CommandHandler("mute", handlers.mute_command))
    dp.add_handler(CommandHandler("addtrigger", handlers.add_trigger_command))
    dp.add_handler(CommandHandler("deltrigger", handlers.delete_trigger_command))
    dp.add_handler(CommandHandler("newchat", handlers.new_chat_command))
    dp.add_handler(CommandHandler("chatid", handlers.chat_id_command))
    dp.add_handler(CommandHandler("addadmin", handlers.add_admin_command))
    dp.add_handler(CommandHandler("deladmin", handlers.delete_admin_command))
    dp.add_handler(CommandHandler("send", handlers.add_send_permission_command))
    dp.add_handler(CommandHandler("delsend", handlers.delete_send_permission_command))
    dp.add_handler(CommandHandler("vip", handlers.add_vip_command))
    dp.add_handler(CommandHandler("delvip", handlers.delete_vip_command))
    dp.add_handler(CommandHandler("desc", handlers.desc_command))
    dp.add_handler(CommandHandler("top", handlers.top_command))
    dp.add_handler(CommandHandler("menu", handlers.menu_command))
    dp.add_handler(CommandHandler("sort", handlers.sort_command))
    dp.add_handler(CommandHandler("hash", handlers.hash_command))
    dp.add_handler(CommandHandler("dus", handlers.dus_command))
    dp.add_handler(CommandHandler("sd", handlers.sd_command))
    dp.add_handler(CommandHandler("centr", handlers.centr_command))
    dp.add_handler(CommandHandler("pervak", handlers.pervak_command))
    dp.add_handler(CommandHandler("shala", handlers.shala_command))
    dp.add_handler(CommandHandler("trim", handlers.trim_command))
    dp.add_handler(CommandHandler("wax", handlers.wax_command))
    dp.add_handler(CommandHandler("mushrooms", handlers.mushrooms_command))
    dp.add_handler(CommandHandler("cannafood", handlers.cannafood_command))
    dp.add_handler(CallbackQueryHandler(handlers.button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handlers.handle_message))
    updater.start_polling()
    scheduler = BackgroundScheduler()
    scheduler.start()
    updater.idle()

if __name__ == '__main__':
    main()
