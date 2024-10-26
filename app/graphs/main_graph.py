from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables.config import RunnableConfig
from ..schemas.state import State
from ..services.llm import llm
from ..logger import setup_logger
from langchain_core.output_parsers import StrOutputParser
from ..database.vector_store import get_vectorstore

logger = setup_logger(__name__)

graph = StateGraph(State)

general_answer = """Данный вопрос определен как не связанный с руководством пользователя, пожалуйста попробуйте снова или обратитесь в наш отдел технической поддержки."""

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
        "summary":index,
        "user_context":"\n".join([el[1] for el in state["last_messages"] if el[0] == "user"]),
        "user_message":state["user_message"]
    })
    if response.replace("'", "").lower() == "нет" or response.replace("'", "").lower().endswith("нет"):
        return {"is_index":False, "answer":general_answer, "rel_docs":[]}
    else:
        return {"is_index":True}

def route_index(state:State) -> Literal["get_relevant_docs", "__end__"]:
    if state["is_index"]:
        return "get_relevant_docs"
    else:
        return END

# doc_schema:
# {"1.1.1(.1)":{"text":str, "images":list[str]("paths")}}
# {"1.1.1.1":Document()}

async def get_relevant_docs(state:State) -> State:
    vectorstore = get_vectorstore()
    return {'rel_docs':[{el.metadata["chapter"]:{"text":el.page_content, "images":el.metadata["image_paths"]}} for el in await vectorstore.asimilarity_search(query=state["db_query"])]}

async def score_docs(state:State)->State:
    new_rel_docs=[]
    prompt_template="""
    Ты - оператор чат бота помощника по руководству по сайту Сила. Твоя задача по предоставленному запросу пользователя определить является ли предложенный раздел документации подходящим.
    В руководстве могут быть описаны инструкции, помощь с обработкой ошибок, навигацией по сайту. Ответ должен состоять из одного слова, либо 'Да', либо 'Нет'.
    Отвечай 'Да' если документ релевантен запросу и его можно учитывать при генерации ответа.
    Отвечай 'Нет' если документ не поможет пользователю в решении вопроса или он второстепенный. 
    Важно не путать пользователя лишними инструкциями поэтому определяй осторожно.
    
    Текущий вопрос пользователя:
    
    {user_message}
    
    Документ на оценку:
    
    {doc_check}
    
    Ответ:"""
    prompt = PromptTemplate.from_template(prompt_template)
    bound = prompt | llm | StrOutputParser()
    for doc in state["rel_docs"]:
        response = await bound.ainvoke({
            "user_message":state["user_message"],
            "doc_check":doc.values()["text"]
        })
        if response.replace("'", "").lower() == "нет" or response.replace("'", "").lower().endswith("нет"):
            continue
        else:
            new_rel_docs.append(doc)
    if len(new_rel_docs) == 0:
        return {"rewrite":True, "rel_docs":[], "retries":state['retries'] + 1}
    else:
        return {"rewrite":False, "rel_docs":new_rel_docs}

contact_message = """Ответ на ваш вопрос не найден среди документов руководства пользователя. Если Вам требуется квалифицированная помощь, позвоните на телефон «горячей линии поддержки», напишите письмо или воспользуйтесь формой регистрации заявки на сайте. 
КОНТАКТНАЯ ИНФОРМАЦИЯ
Техническая поддержка
+7 (495) 258-06-36
info@lense.ru
lense.ru
"""

def route_docs(state:State) -> Literal["rewrite_query", "no_docs", "generate"]:
    if state["retries"] >= 2:
        return "no_docs"
    elif state["rewrite"]:
        return "rewrite_query"
    else:
        return "generate"


async def rewrite_query(state:State) -> State:
    prompt_template = """Ты - оператор чат бота, помощника пользователя по сайту Сила. Чат бот проводит поиск релевантных документов из руководства пользователя для ответа на вопрос.
    Прошлый поиск не удался, поэтому твоя задача перефразировать и изменить запрос к векторной базе данных привел к правильным результатом.
    Твой ответ должен быть строкой, которая упоминает нужные компоненты или действия на сайте. Перефразируй запрос пользователя более формально, чтобы по ключевым словам и смыслу запроса нашшлись нужные документы.
    Краткая выжимка из руководства пользователя:
    
    {summary}
    
    Сообщение пользователя:
    
    {user_message}
    
    Неудавшийся запрос:

    {last_query}

    Ответ:"""
    prompt = PromptTemplate.from_template(prompt_template)
    bound = prompt | llm | StrOutputParser()
    with open("index_summary.txt", "r") as f:
        index = f.read()
    return {await bound.ainvoke({"summary": index, "user_message":state['user_message'], "last_query":state["db_query"]})}


def no_docs(state:State) -> State:
    return {"answer":contact_message}


