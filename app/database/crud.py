from typing import Dict, Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .models import ChatMessage


async def create_chat_message(db: AsyncSession, user_id: str, sender_role: str,
                              content: Dict[str, Any]) -> models.ChatMessage:
    db_message = models.ChatMessage(user_id=user_id, sender_role=sender_role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_chat_history(db: AsyncSession, user_id: str, branch_id: str, limit: int = 10) -> Sequence[ChatMessage]:
    query = select(models.ChatMessage).where(models.ChatMessage.user_id == user_id).order_by(
        models.ChatMessage.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_chat_history_by_branch_id(db: AsyncSession, user_id: str, branch_id: str) -> Sequence[ChatMessage]:
    query = (select(models.ChatMessage).where(models.ChatMessage.user_id == user_id,
                                              models.ChatMessage.branch_id == branch_id)
             .order_by(models.ChatMessage.timestamp.desc()))
    result = await db.execute(query)
    return result.scalars().all()


async def create_branch(db: AsyncSession, user_id: str):
    db_branch = models.ChatBranch(user_id=user_id)
    db.add(db_branch)
    await db.commit()
    await db.refresh(db_branch)
    return db_branch


async def get_last_five_branch_answers(db: AsyncSession, user_id: str, limit: int = 5):
    query = (select(models.ChatBranch.id, models.ChatMessage.user_id)
             .join(target=ChatMessage, user_id=user_id)
             .where()
             .order_by(models.ChatMessage.timestamp.desc())).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


