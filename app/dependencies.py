# app/dependencies.py

from fastapi import Depends
from fastapi import HTTPException
from app.main import app
from app.services.model_loader import ModelLoader

def get_model_loader() -> ModelLoader:
    model_loader = getattr(app.state, "model_loader", None)
    if not model_loader:
        raise HTTPException(status_code=500, detail="Модель ещё не загружена")
    return model_loader
