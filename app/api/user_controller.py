import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal, get_db
from app.database.crud import create_chat_message
from app.schemas.state import State

main_graph = None

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global main_graph
#     async with AsyncSessionLocal() as db:
#         await update_router_parser(db)
#         main_graph = await create_main_graph(db)
#     yield


app = FastAPI(lifespan=lifespan)


@app.post("/api/v1/user")
async def newUser():
    try:
        return {"user_id": uuid.uuid4()}
    except Exception as e:
        logger.exception("An error occurred during chat processing")
        raise HTTPException(status_code=500, detail=str(e))
