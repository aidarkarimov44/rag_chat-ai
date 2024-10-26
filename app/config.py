from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    YANDEXGPT_IAM_TOKEN:str=os.getenv("YANDEXGPT_IAM_TOKEN")
    YANDEXGPT_MODEL_URI:str=os.getenv("YANDEXGPT_MODEL_URI")


settings = Settings()