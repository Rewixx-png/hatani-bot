import asyncio
from aiogram.types import Message

async def send_chunked_message(message: Message, text: str):
    if not text:
        return

    MAX_LENGTH = 4000
    
    if len(text) <= MAX_LENGTH:
        await message.answer(text, parse_mode="Markdown")
        return

    parts = []
    while len(text) > 0:
        if len(text) > MAX_LENGTH:
            split_pos = text.rfind('\n', 0, MAX_LENGTH)
            if split_pos == -1:
                split_pos = text.rfind(' ', 0, MAX_LENGTH)
            
            if split_pos == -1:
                split_pos = MAX_LENGTH
            
            chunk = text[:split_pos]
            parts.append(chunk)
            text = text[split_pos:].lstrip()
        else:
            parts.append(text)
            break

    for part in parts:
        await message.answer(part, parse_mode="Markdown")
        await asyncio.sleep(0.3)