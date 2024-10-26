from functools import lru_cache
from langchain_postgres import PGVector
from ..config import settings
from ..chunks_creating import documents
from langchain_community.embeddings import GigaChatEmbeddings
# from langchain.embeddings.base import Embeddings
import time
import requests
from typing import Any, List, Mapping, Optional
# from langchain.callbacks.manager import CallbackManagerForLLMRun
import requests
import langchain
import os
# class YandexGPTEmbeddings(Embeddings):

#     def __init__(self, iam_token=None, api_key=None, folder_id=None, sleep_interval=1):
#         self.iam_token = iam_token
#         self.sleep_interval = sleep_interval
#         self.api_key = api_key
#         self.folder_id = folder_id
#         if self.iam_token:
#             self.headers = {'Authorization': 'Bearer ' + self.iam_token}
#         if self.api_key:
#             self.headers = {'Authorization': 'Api-key ' + self.api_key,
#                              "x-folder-id" : self.folder_id }
                
#     def embed_document(self, text):
#         j = {
#           "model" : "general:embedding",
#           "embedding_type" : "EMBEDDING_TYPE_DOCUMENT",
#           "text": text
#         }
        
#         res = requests.post("https://llm.api.cloud.yandex.net/llm/v1alpha/embedding",
#                             json=j, headers=self.headers)
#         print(res)
#         vec = res.json()['embedding']
#         return vec

#     def embed_documents(self, texts, chunk_size = 0):
#         res = []
#         for x in texts:
#             res.append(self.embed_document(x))
#             time.sleep(self.sleep_interval)
#         return res
        
#     def embed_query(self, text):
#         j = {
#           "model" : "general:embedding",
#           "embedding_type" : "EMBEDDING_TYPE_QUERY",
#           "text": text
#         }
#         res = requests.post("https://llm.api.cloud.yandex.net/llm/v1alpha/embedding",
#                             json=j,headers=self.headers)
#         vec = res.json()['embedding']
#         time.sleep(self.sleep_interval)
#         return vec

@lru_cache
def get_vectorstore() -> PGVector:
    # embeddings = YandexGPTEmbeddings(iam_token=settings.YANDEXGPT_IAM_TOKEN)
    embeddings = GigaChatEmbeddings(credentials=settings.GIGACHAT_CREDENTIALS, verify_ssl_certs=False, scope="GIGACHAT_API_PERS")
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=settings.PG_COLLECTION_NAME,
        connection=settings.PG_CONNECTION,
        use_jsonb=True,
        async_mode=True,
    )
    return vectorstore
