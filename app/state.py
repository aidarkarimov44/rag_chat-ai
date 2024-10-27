# app/state.py

from typing import Optional, List
from langchain.schema import Document
from rank_bm25 import BM25Okapi

class AppState:
    bm25: Optional[BM25Okapi] = None
    bm25_documents: Optional[List[Document]] = None

app_state = AppState()
