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

    if chat_id == user_id:
        return True
        
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
        return True
        
    if chat_id in ALLOWED_GROUP_IDS:
        # Для групп без топиков message_thread_id равен None.
        # Для General топика он может быть равен message_thread_id топика или None.
        # В новой группе (-1002626866719) топиков нет, поэтому проверка thread_id не должна блокировать ответ.
        # Логика: если это разрешенная группа, рандомим ответ.
        
        # Если нужно сохранить логику "только General" для старой группы, можно усложнить,
        # но обычно для "group without topics" message_thread_id всегда None.
        
        is_topic_message = message.is_topic_message if hasattr(message, 'is_topic_message') else False
        
        # Разрешаем отвечать рандомно, если это не специфичный топик (или если топиков нет вообще)
        # Если в старой группе вы хотите отвечать ТОЛЬКО в General (id=1 или None), оставьте проверку.
        # Но для универсальности лучше просто чекать шанс.
        
        if random.random() < 0.135:
            return True

    return False