import random
from aiogram.types import Message
from app.core.config import ALLOWED_GROUP_ID, ALLOWED_USER_ID

async def is_allowed(message: Message) -> bool:
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id == ALLOWED_GROUP_ID:
        return True
    
    if user_id == ALLOWED_USER_ID:
        return True
        
    return False

async def should_reply(message: Message) -> bool:
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_id = message.bot.id

    if chat_id == user_id:
        return True
        
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
        return True
        
    if chat_id == ALLOWED_GROUP_ID:
        if message.message_thread_id == 1 or message.message_thread_id is None:
            if random.random() < 0.27:
                return True

    return False