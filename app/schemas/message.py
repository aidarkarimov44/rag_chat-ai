# app/schemas/message.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
import base64

class MessageImage(BaseModel):
    filename: str
    data: str  # Base64-encoded image data

    @validator('data')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError('Invalid base64 encoding')
        return v

class SendMessageRequest(BaseModel):
    user_id: str
    chat_id: int
    message: str
    images: Optional[List[MessageImage]] = None  # Опционально список изображений

class PhotoInfo(BaseModel):
    chapter: str
    image_number: str
    base64_data: str  # Base64-encoded image data

class SendMessageResponse(BaseModel):
    user_message: str
    bot_answer: str
    photos: List[PhotoInfo]
