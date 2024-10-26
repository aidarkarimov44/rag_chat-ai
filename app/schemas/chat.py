# app/schemas/chat.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageSchema(BaseModel):
    sender: str
    content: str
    timestamp: Optional[datetime] = None

class ChatHistoryResponse(BaseModel):
    messages: List[MessageSchema]
