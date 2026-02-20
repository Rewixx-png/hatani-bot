import random
from aiogram.types import Message
from app.core.config import ALLOWED_GROUP_IDS, ALLOWED_USER_IDS

async def is_allowed(message: Message) -> bool:
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id in ALLOWED_GROUP_IDS:
        return True
    
    if user_id in ALLOWED_USER_IDS:
        return True
        
    return False

async def should_reply(message: Message) -> bool:
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_id = message.bot.id

    # В личных сообщениях отвечаем всегда
    if chat_id == user_id:
        return True
        
    # Если это реплай на сообщение бота - отвечаем
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
        return True
    
    # Спонтанные ответы (random) ПОЛНОСТЬЮ ОТКЛЮЧЕНЫ.
    # Бот теперь отвечает ТОЛЬКО если к нему обратились (реплай) или в ЛС.
    return False