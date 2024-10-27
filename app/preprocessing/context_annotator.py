from langchain.prompts import PromptTemplate
from ..services.llm import llm_light

ANNOTATION_PROMPT = """
Ты - помощник, который добавляет важный контекст к фрагментам документации.
Твоя задача - создать краткое описание контекста для данного фрагмента текста.

Текст: {text}

Создай одно предложение, описывающее:
1. К какому разделу руководства относится этот фрагмент
2. Какую основную тему или функциональность он описывает
3. Как он связан с другими частями системы

Формат: "Этот фрагмент относится к [раздел]; описывает [тема]; связан с [связи]."

Контекст:"""

class ContextAnnotator:
    def __init__(self):
        self.prompt = PromptTemplate(
            template=ANNOTATION_PROMPT,
            input_variables=["text"]
        )
        
    async def annotate_chunk(self, chunk_text: str, metadata: dict) -> str:
        """Добавляет контекстную аннотацию к чанку"""
        try:
            # Получаем контекст от модели
            context = await self.prompt.aformat_prompt(text=chunk_text)
            context = await llm_light.ainvoke(context)
            
            # Объединяем контекст с оригинальным текстом
            return f"{context}\n\n{chunk_text}"
        except Exception as e:
            print(f"Ошибка при аннотации чанка: {e}")
            return chunk_text
