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
    return
    
    await try_react_clown(message)
    
    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        is_reply = True

    should_process = await should_reply(message)
    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=message.caption or "", image_base64=None)
        return

    wait_msg = await message.answer("Ща гляну че ты там высрал...")
    
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        caption = message.caption or "Обосри это изображение максимально жестоко."
        
        await mistral.add_user_message(message.chat.id, text=caption, image_base64=base64_image)
        response = await mistral.get_response(message.chat.id)
        
        await send_chunked_message(message, response, reply_to_message_id=message.message_id)
    except Exception as e:
        await message.answer(f"Слышь, у меня глаз выпал от твоей хуйни: {str(e)}")
    finally:
        await wait_msg.delete()

@router.message(F.video | F.animation)
async def handle_video(message: Message, bot: Bot):
    return
    
    await try_react_clown(message)

    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        is_reply = True

    should_process = await should_reply(message)
    
    caption = message.caption or ""
    content_type = "Animation" if message.animation else "Video"
    user_text = caption if caption else f"[{content_type} sent]"

    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=user_text)
        return

    wait_msg = await message.answer(f"Пырюсь в твое {content_type.lower()}...")

    try:
        thumb = None
        if message.video and message.video.thumbnail:
            thumb = message.video.thumbnail
        elif message.animation and message.animation.thumbnail:
            thumb = message.animation.thumbnail

        if thumb:
            file_io = io.BytesIO()
            await bot.download(thumb.file_id, destination=file_io)
            image_bytes = file_io.getvalue()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = caption or f"Унизь автора этого {content_type.lower()}."
            await mistral.add_user_message(message.chat.id, text=prompt, image_base64=base64_image)
        else:
            prompt = caption or f"User sent a {content_type} without a thumbnail."
            await mistral.add_user_message(message.chat.id, text=prompt)

        response = await mistral.get_response(message.chat.id)
        await send_chunked_message(message, response, reply_to_message_id=message.message_id)

    except Exception as e:
        logging.error(f"Video handling error: {e}")
        await message.answer(f"Ты даже видео нормально скинуть не можешь, уебан: {str(e)}")
    finally:
        await wait_msg.delete()

@router.message(F.text)
async def handle_text(message: Message):
    await try_react_clown(message)

    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        is_reply = True

    should_process = await should_reply(message)

    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=message.text or "")
        return

    try:
        await mistral.add_user_message(message.chat.id, text=message.text or "")
        response = await mistral.get_response(message.chat.id)
        await send_chunked_message(message, response, reply_to_message_id=message.message_id)
    except Exception as e:
        await message.answer(f"Я сломался от твоей тупости: {str(e)}")
