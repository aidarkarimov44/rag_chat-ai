# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import List

class LastMessageSchema(BaseModel):
    sender: str
    content: str
    timestamp: datetime

class ChatWithLastMessageResponse(BaseModel):
    chat_id: int
    last_message: LastMessageSchema
