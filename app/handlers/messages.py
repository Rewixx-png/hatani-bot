import io
import base64
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from app.handlers.filters import should_reply
from app.services.mistral import MistralService
from app.utils.text import send_chunked_message

router = Router()
mistral = MistralService()

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        is_reply = True

    should_process = await should_reply(message)
    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=message.caption or "", image_base64=None)
        return

    wait_msg = await message.answer("Анализирую фото...")
    
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        caption = message.caption or "Что на этом изображении?"
        
        await mistral.add_user_message(message.chat.id, text=caption, image_base64=base64_image)
        response, thinking = await mistral.get_response(message.chat.id)
        
        if thinking:
            thinking_msg = await message.answer(f"💭 *Thinking:*\n{thinking}", parse_mode="Markdown")
        
        await send_chunked_message(message, response)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    finally:
        await wait_msg.delete()

@router.message(F.video | F.animation)
async def handle_video(message: Message, bot: Bot):
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

    wait_msg = await message.answer(f"Смотрю {content_type.lower()}...")

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
            
            prompt = caption or f"Проанализируй этот кадр из {content_type.lower()}."
            await mistral.add_user_message(message.chat.id, text=prompt, image_base64=base64_image)
        else:
            prompt = caption or f"User sent a {content_type} without a thumbnail."
            await mistral.add_user_message(message.chat.id, text=prompt)

        response, thinking = await mistral.get_response(message.chat.id)
        
        if thinking:
            thinking_msg = await message.answer(f"💭 *Thinking:*\n{thinking}", parse_mode="Markdown")
        
        await send_chunked_message(message, response)

    except Exception as e:
        logging.error(f"Video handling error: {e}")
        await message.answer(f"Ошибка при обработке видео: {str(e)}")
    finally:
        await wait_msg.delete()

@router.message(F.text)
async def handle_text(message: Message):
    is_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        is_reply = True

    should_process = await should_reply(message)

    if not should_process and not is_reply:
        await mistral.add_user_message(message.chat.id, text=message.text or "")
        return

    try:
        await mistral.add_user_message(message.chat.id, text=message.text or "")
        response, thinking = await mistral.get_response(message.chat.id)
        
        if thinking:
            thinking_msg = await message.answer(f"💭 *Thinking:*\n{thinking}", parse_mode="Markdown")
        
        await send_chunked_message(message, response)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
