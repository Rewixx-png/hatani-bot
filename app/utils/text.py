import asyncio
from aiogram.types import Message
from typing import Optional

async def send_chunked_message(message: Message, text: str, reply_to_message_id: Optional[int] = None):
    if not text:
        return

    MAX_LENGTH = 4000
    
    if len(text) <= MAX_LENGTH:
        await message.answer(text, parse_mode="Markdown", reply_to_message_id=reply_to_message_id)
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

    for i, part in enumerate(parts):
        reply_id = reply_to_message_id if i == 0 else None
        await message.answer(part, parse_mode="Markdown", reply_to_message_id=reply_id)
        await asyncio.sleep(0.3)

async def send_chunked_message_html(message: Message, text: str, reply_to_message_id: Optional[int] = None):
    if not text:
        return

    MAX_LENGTH = 4000
    
    if len(text) <= MAX_LENGTH:
        await message.answer(text, parse_mode="HTML", reply_to_message_id=reply_to_message_id)
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

    for i, part in enumerate(parts):
        reply_id = reply_to_message_id if i == 0 else None
        await message.answer(part, parse_mode="HTML", reply_to_message_id=reply_id)
        await asyncio.sleep(0.3)
