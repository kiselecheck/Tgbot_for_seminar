from imports_all import *

from handlers import send_msg, router, set_commands
from config import tg_bot_token
from BD import SomeMiddleware, start_db

bot = Bot(token=tg_bot_token)
dp = Dispatcher()

logging.basicConfig(force=True, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('logs.log'),
                        logging.StreamHandler()
                    ]
                    )
logger = logging.getLogger(__name__)

async def main():
    dp.include_router(router)
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    job = scheduler.add_job(send_msg, 'interval', seconds=120, args=(bot,))
    scheduler.start()
    dp.message.outer_middleware(SomeMiddleware())
    dp.startup.register(start_db)
    await set_commands(bot)
    try:
        logging.info("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logging.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())
