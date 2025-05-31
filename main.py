# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, LOG_FILE, LOG_LEVEL
from handlers import router as handlers_router
from admin import router as admin_router
from triggers import router as triggers_router
from database import Database

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🤖 **Запуск бота...**")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    db = Database("bot_database.db")
    logger.info("✅ **База данных инициализирована**")
    
    dp.include_router(handlers_router)
    dp.include_router(admin_router)
    dp.include_router(triggers_router)
    
    logger.info("🤖 **Бот успешно запущен**")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ **Ошибка при запуске бота**: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    print("Запускаю main.py...")
    asyncio.run(main())