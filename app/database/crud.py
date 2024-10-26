from typing import Dict, Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .models import ChatMessage


async def create_chat_message(db: AsyncSession, user_id: str, sender_role: str, content: Dict[str, Any]) -> models.ChatMessage:
    db_message = models.ChatMessage(user_id=user_id, sender_role=sender_role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_history(db: AsyncSession, user_id: str, limit: int = 10) -> Sequence[ChatMessage]:
    query = select(models.ChatMessage).where(models.ChatMessage.user_id == user_id).order_by(models.ChatMessage.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

