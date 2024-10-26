from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .user import User
from .document import Document

async def create_user(session: AsyncSession, user_id: str, thread_id: str):
    user = User(user_id=user_id, thread_id=thread_id)
    session.add(user)
    await session.commit()
    return user

async def get_user_by_user_id(session: AsyncSession, user_id: str):
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def create_document(session: AsyncSession, filename: str, content: str, user_id: int):
    document = Document(filename=filename, content=content, user_id=user_id)
    session.add(document)
    await session.commit()
    return document

async def get_documents_by_user(session: AsyncSession, user_id: str):
    result = await session.execute(select(Document).where(Document.user_id == user_id))
    return result.scalars().all()
