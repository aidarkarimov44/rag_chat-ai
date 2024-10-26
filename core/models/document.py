# core/models/document.py
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Document(Base):
    filename: Mapped[str]
    content: Mapped[str]
    user_id: Mapped[str]