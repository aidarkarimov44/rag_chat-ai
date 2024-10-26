# app/schemas/user.py
from pydantic import BaseModel

class UserCreateResponse(BaseModel):
    user_id: str
