from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class User(Base):
    user_id: Mapped[str] = mapped_column(unique=True, index=True)
    thread_id: Mapped[str] = mapped_column(unique=True)