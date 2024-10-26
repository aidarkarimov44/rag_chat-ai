# app/schemas/message.py
from pydantic import BaseModel
from typing import List, Optional

class SendMessageResponse(BaseModel):
    user_message: str
    bot_answer: str
    photos: List[dict]
