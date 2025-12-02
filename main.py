import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import config
from database import db
from handlers import register_handlers
from scheduler import TaskScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция"""

    # Проверка токена
    if not config.BOT_TOKEN:
        print("ОШИБКА: BOT_TOKEN не задан!")
        return

    try:
        # Инициализация базы данных
        await db.init()

        # Создание бота
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # Проверка доступности бота
        me = await bot.get_me()
        print(f"Бот запущен: @{me.username}")

        # Настройка диспетчера
        dp = Dispatcher()
        register_handlers(dp)

        # Запуск планировщика
        scheduler = TaskScheduler(bot)
        scheduler.start()

        print("Бот готов к работе!")

        # Запуск поллинга
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
    finally:
        try:
            await scheduler.shutdown()
            await bot.session.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
