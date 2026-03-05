# src/services/gemini_ocr.py
import base64
import os
from dotenv import load_dotenv
from api.llm_utils import extract_text_from_image

def extract_text_from_image_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    # We call it 'gemini' in name but it's now OpenRouter (which can use Gemini)
    return extract_text_from_image(
        image_bytes, 
        "Extract all alphanumeric text from the image. Return plain text only.",
        mime_type=mime_type
    )
