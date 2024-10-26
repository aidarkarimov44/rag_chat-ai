from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    YANDEXGPT_IAM_TOKEN:str=os.getenv("YANDEXGPT_IAM_TOKEN")
    YANDEXGPT_MODEL_URI:str=os.getenv("YANDEXGPT_MODEL_URI")
    YANDEXGPT_MAIN_MODEL_URI:str=os.getenv("YANDEX_MAIN_MODEL_URI")
    EMBEDDINGS_MODEL:str=os.getenv("EMBEDDINGS_MODEL")
    DEVICE:str=os.getenv("DEVICE")
    PG_CONNECTION:str=os.getenv("PG_CONNETCTION")
    PG_COLLECTION_NAME:str=os.getenv("PG_COLLECTION_NAME")


settings = Settings()