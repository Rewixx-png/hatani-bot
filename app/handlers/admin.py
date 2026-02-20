from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.services.mistral import MistralService

router = Router()
mistral = MistralService()

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await mistral.clear_history(message.chat.id)
    # Используем жесткий ответ, чтобы соответствовать стилю, но подтвердить действие
    await message.answer("🗑 Память форматирована. Я забыл всё, что ты тут высрал.", parse_mode="Markdown")