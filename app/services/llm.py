from ..config import settings
from langchain_community.llms import YandexGPT

llm_light = YandexGPT(iam_token=settings.YANDEXGPT_IAM_TOKEN, model_uri=settings.YANDEXGPT_MODEL_URI)
# llm_pro = YandexGPT(iam_token=settings.YANDEXGPT_IAM_TOKEN, model_uri=settings.YANDEXGPT_MAIN_MODEL_URI)