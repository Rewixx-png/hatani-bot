import json
import logging
import httpx
from app.core.config import CUSTOM_API_URL, CUSTOM_API_KEY, CUSTOM_MODEL

class CustomProviderService:
    def __init__(self):
        self.base_url = CUSTOM_API_URL.rstrip("/")
        self.api_key = CUSTOM_API_KEY
        self.model = CUSTOM_MODEL
        
    async def chat_complete(self, messages: list) -> dict:
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    def parse_response(self, response: dict) -> str:
        return response["choices"][0]["message"]["content"].strip()
