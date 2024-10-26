from ..config import settings
from langchain_community.llms import YandexGPT

llm = YandexGPT(iam_token=settings.YANDEXGPT_IAM_TOKEN, model_uri=settings.YANDEXGPT_MODEL_URI)
