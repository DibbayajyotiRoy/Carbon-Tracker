import os
import httpx
import json
import base64
from typing import Optional, List, Dict, Any

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def call_llm(
    messages: List[Dict[str, Any]], 
    response_format: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None
) -> str:
    """
    Generic call to OpenRouter with OpenAI-compatible payload.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model or LLM_MODEL,
        "messages": messages,
    }
    
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

async def extract_text_from_image(
    image_bytes: bytes, 
    prompt: str, 
    mime_type: str = "image/jpeg"
) -> str:
    """
    Vision-enabled request via OpenRouter.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64_image}"
                    }
                }
            ]
        }
    ]
    
    return await call_llm(messages)
