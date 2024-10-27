# app/dependencies.py

from fastapi import Depends, Request, HTTPException
from app.services.model_loader import ModelLoader

async def get_model_loader(request: Request) -> ModelLoader:
    model_loader = getattr(request.app.state, "model_loader", None)
    if not model_loader:
        raise HTTPException(status_code=500, detail="Модель ещё не загружена")
    return model_loader
