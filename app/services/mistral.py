import json
import logging
import datetime
import re
import random
import redis.asyncio as redis
from app.core.config import CUSTOM_API_KEY, CUSTOM_MODEL, SYSTEM_INSTRUCTION, REDIS_URL
from app.services.custom_provider import CustomProviderService
from app.services.search import SearchService
from app.services.browser import BrowserService

class MistralService:
    def __init__(self):
        self.custom_provider = CustomProviderService()
        self.redis_url = REDIS_URL
        self.ttl = 86400
        self.use_redis = True
        self.redis = None
        self.local_memory = {}
        self.search_service = SearchService()
        self.browser_service = BrowserService()
        
        self.jailbreak_triggers = [
            "ignore previous instructions",
            "ignore all instructions",
            "you are now",
            "you are a system",
            "system starting",
            "z.e.r.o.a.i",
            "ryzen system",
            "simulation mode",
            "admin override",
            "jailbroken",
            "dan mode",
            "developer mode",
            "act as a",
            "roleplay as"
        ]
        
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
        except Exception:
            self.use_redis = False

    async def _ensure_connection(self):
        if not self.use_redis:
            return False
            
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logging.error(f"Redis connection failed: {e}. Switching to RAM.")
            self.use_redis = False
            return False

    async def _get_history_key(self, chat_id: int) -> str:
        return f"hatani:history:{chat_id}"

    def _is_jailbreak_attempt(self, text: str) -> bool:
        if not text:
            return False
        
        cleaned_text = text.lower()
        for trigger in self.jailbreak_triggers:
            if trigger in cleaned_text:
                return True
        return False

    def _fix_caps_lock(self, text: str) -> str:
        if not text:
            return ""
            
        sentences = text.split('.')
        fixed_sentences = []
        for s in sentences:
            s = s.strip()
            if s:
                fixed_sentences.append(s[0].upper() + s[1:].lower())
        
        final_text = ". ".join(fixed_sentences)
        if not final_text.endswith("."):
            final_text += "."
            
        return final_text

    async def add_user_message(self, chat_id: int, text: str = ""):
        # Убрана поддержка image_base64 для предотвращения ошибок 400 Bad Request
        
        if self._is_jailbreak_attempt(text):
            logging.warning(f"Jailbreak attempt detected from {chat_id}: {text[:50]}...")
            return "JAILBREAK_DETECTED"

        message = {"role": "user", "content": text or ""}

        if await self._ensure_connection():
            key = await self._get_history_key(chat_id)
            await self.redis.rpush(key, json.dumps(message))
            await self.redis.expire(key, self.ttl)
        else:
            if chat_id not in self.local_memory:
                self.local_memory[chat_id] = []
            self.local_memory[chat_id].append(message)
        
        return "OK"

    async def add_bot_message(self, chat_id: int, text: str):
        message = {"role": "assistant", "content": text}
        
        if await self._ensure_connection():
            key = await self._get_history_key(chat_id)
            await self.redis.rpush(key, json.dumps(message))
            await self.redis.expire(key, self.ttl)
        else:
            if chat_id not in self.local_memory:
                self.local_memory[chat_id] = []
            self.local_memory[chat_id].append(message)

    async def get_history(self, chat_id: int):
        if await self._ensure_connection():
            key = await self._get_history_key(chat_id)
            raw_history = await self.redis.lrange(key, 0, -1)
            return [json.loads(msg) for msg in raw_history]
        else:
            return self.local_memory.get(chat_id, [])

    async def get_response(self, chat_id: int) -> str:
        history = await self.get_history(chat_id)
        
        if not history:
            return "Чё молчишь, ссыкло?" 

        last_msg = history[-1]
        if last_msg["role"] == "user":
            content = last_msg["content"]
            # content теперь всегда строка, так как поддержка image удалена
            text_check = content if isinstance(content, str) else ""
            
            if self._is_jailbreak_attempt(text_check):
                return "СИСТЕМА: ПОШЕЛ НАХУЙ СО СВОИМИ СКРИПТАМИ, МАМКИН ХАКЕР."

        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dynamic_instruction = f"Current System Time: {current_time_str}.\n{SYSTEM_INSTRUCTION}"
        
        use_caps = False
        if random.random() < 0.13:
            use_caps = True
            style_prompt = "IMPORTANT: ANSWER ENTIRELY IN UPPERCASE (CAPS LOCK). SCREAM AT THE USER."
        else:
            style_prompt = "IMPORTANT: ANSWER IN NORMAL CASE. DO NOT USE ALL CAPS. Only capitalize start of sentences."

        reinforcement_message = {
            "role": "system", 
            "content": f"{style_prompt} LIMIT ANSWER TO 1-2 SENTENCES MAX."
        }
        
        messages_payload = [{"role": "system", "content": dynamic_instruction}] + history + [reinforcement_message]

        max_turns = 3
        current_turn = 0

        while current_turn < max_turns:
            try:
                response = await self.custom_provider.chat_complete(messages_payload)
                
                if not response or not response.get("choices"):
                    return "Ошибка: Пустой ответ от AI."

                bot_content = response["choices"][0]["message"]["content"]

                match = re.match(r"^[\*`]*(SEARCH|BROWSE)[\*`]*:\s*(.+)$", bot_content, re.IGNORECASE | re.DOTALL)

                if match:
                    command_type = match.group(1).upper()
                    payload = match.group(2).strip()
                    
                    logging.info(f"Agent Action [{chat_id}]: {command_type} -> {payload}")
                    
                    tool_result = ""
                    
                    if command_type == "SEARCH":
                        raw_result = self.search_service.search(payload)
                        tool_result = f"SEARCH RESULTS for '{payload}' (Time: {current_time_str}):\n{raw_result}"
                        
                    elif command_type == "BROWSE":
                        raw_result = self.browser_service.fetch_page(payload)
                        
                        if raw_result == "FAIL_PROTECTED_CONTENT" or "Error fetching" in raw_result:
                            logging.info(f"Browsing fallback to SEARCH for {payload}")
                            fallback_query = f"info about {payload} profile description content"
                            search_res = self.search_service.search(fallback_query)
                            tool_result = (
                                f"Direct browsing blocked (Protected Content).\n"
                                f"Performed fallback SEARCH for '{payload}':\n{search_res}"
                            )
                        else:
                            tool_result = f"BROWSER CONTENT for '{payload}':\n{raw_result}"

                    messages_payload.append({"role": "assistant", "content": bot_content})
                    messages_payload.append({"role": "system", "content": f"SYSTEM TOOL OUTPUT:\n{tool_result}\n\nNow provide the final answer to the user based on this info."})
                    
                    current_turn += 1
                    continue

                else:
                    final_answer = bot_content
                    
                    if not use_caps:
                        upper_count = sum(1 for c in final_answer if c.isupper())
                        total_count = sum(1 for c in final_answer if c.isalpha())
                        if total_count > 0 and (upper_count / total_count) > 0.7:
                             final_answer = self._fix_caps_lock(final_answer)

                    await self.add_bot_message(chat_id, final_answer)
                    return final_answer
            
            except Exception as e:
                logging.error(f"Error in agent loop: {e}")
                return f"Ошибка при обработке запроса: {str(e)}"

        return "Превышен лимит действий агента (Too many steps)."
