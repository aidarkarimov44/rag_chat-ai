from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from ..config import settings

@lru_cache
def get_vectorstore() -> PGVector:
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDINGS_MODEL,
        model_kwargs={"device": settings.DEVICE}
    )
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=settings.PG_COLLECTION_NAME,
        connection=settings.PG_CONNECTION,
        use_jsonb=True,
        async_mode=True,
    )
    return vectorstore

