from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables.config import RunnableConfig
from ..schemas.state import State
from ..services.llm import llm
from ..logger import setup_logger
from langchain_core.output_parsers import StrOutputParser
from ..services.vector_store import get_vectorstore

logger = setup_logger(__name__)

graph = StateGraph(State)

async def classify_index(state:State) -> State:  # -> Literal["index", "general"]:
    with open("index_summary.txt", "r") as f:
        index = f.read()
    prompt_template = """
    Ты - оператор чат бота, задача которого отвечать на вопросы пользователей связанные с руководством приложения. Ты должен определить связан ли вопрос конкретно с программой или руководством или он на общую тему.
    Тебе будет дан текущий запрос пользователя и выжимка из руководства пользователя. Ты должен вернуть ответ строго одним словом, либо 'Да' либо 'Нет'.
    Напиши 'Да' если текущий вопрос пользователя связан с программой или руководством и 'Нет' если текущий вопрос пользователя идет на отвлеченную тему.
    Выжимка из руководства:

    {summary}

    Последние сообщения пользователя:

    {user_context}

    Текущий вопрос пользователя

    {user_message}

    Ответ:
    """
    prompt = PromptTemplate.from_template(prompt_template)
    bound = prompt | llm | StrOutputParser()
    response:str = await bound.ainvoke({
        "summary":"index",
        "user_context":"\n".join([el[1] for el in state["last_messages"] if el[0] == "user"]),
        "user_message":state["user_message"]
    })
    if response.lower() == "нет" or response.lower().endswith("нет"):
        return {"is_index":False}
    else:
        return {"is_index":True}