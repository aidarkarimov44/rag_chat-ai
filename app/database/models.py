import uuid

from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, index=True)
    branch_id = Column(String, index=True)
    sender_role = Column(String)
    content = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ChatBranch(Base):
    __tablename__ = "chat_branches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


