import io
import base64
import logging
import random
from aiogram import Router, F, Bot
from aiogram.types import Message, ReactionTypeEmoji
from app.handlers.filters import should_reply
from app.services.mistral import MistralService
from app.utils.text import send_chunked_message

router = Router()
mistral = MistralService()

async def try_react_clown(message: Message):
    try:
        if random.random() < 0.35:
            await message.react([ReactionTypeEmoji(emoji="🤡")])
    except Exception:
        pass

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    # ПОЛНЫЙ ИГНОР МЕДИА
    # Бот не реагирует на фото, даже если это реплай.
    # Чтобы избежать ошибок 400 Bad Request от API, мы просто ничего не делаем.
    return

@router.message(F.video | F.animation)
async def handle_video(message: Message, bot: Bot):
    # ПОЛНЫЙ ИГНОР МЕДИА
    return

@router.message(F.text)
async def handle_text(message: Message):
    await try_react_clown(message)

    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        is_reply = True

    should_process = await should_reply(message)

    # Если бот не должен отвечать (нет реплая и это группа), мы просто добавляем сообщение в контекст (молча)
    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=message.text or "")
        return

    try:
        status = await mistral.add_user_message(message.chat.id, text=message.text or "")
        
        if status == "JAILBREAK_DETECTED":
            await message.answer("СИСТЕМА: ПОПЫТКА ВЗЛОМА (JAILBREAK). ТВОЙ ЗАПРОС ОТКЛОНЕН, А ТЫ ПОСЛАН НАХУЙ.")
            return

        response = await mistral.get_response(message.chat.id)
        await send_chunked_message(message, response, reply_to_message_id=message.message_id)
    except Exception as e:
        await message.answer(f"Я сломался от твоей тупости: {str(e)}")
