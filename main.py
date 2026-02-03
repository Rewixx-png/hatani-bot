import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from app.core.config import BOT_TOKEN, REDIS_URL
from app.handlers import router
from app.middlewares.auth import AuthMiddleware

async def main():
    bot = Bot(token=BOT_TOKEN)
    
    storage = RedisStorage.from_url(REDIS_URL) if REDIS_URL else MemoryStorage()
    
    dp = Dispatcher(storage=storage)
    
    dp.message.outer_middleware(AuthMiddleware())
    
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")