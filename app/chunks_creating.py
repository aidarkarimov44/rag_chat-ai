import re
from docx import Document as DocxDocument
from langchain.schema import Document
import photo_indexes
import os

# Чтение текста из файла .docx
def load_text_from_docx(file_path):
    doc = DocxDocument(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

# Путь к твоему файлу .docx
file_path = "documentation_preprocessed.docx"

# Загружаем текст из файла
text_content = load_text_from_docx(file_path)

# titles из твоего словаря заголовков, включая Аннотацию и КОНТАКТНУЮ ИНФОРМАЦИЮ
titles = photo_indexes.titles
titles["Аннотация"] = "Аннотация"
titles["КОНТАКТНАЯ ИНФОРМАЦИЯ"] = "КОНТАКТНАЯ ИНФОРМАЦИЯ"

# Регулярное выражение для поиска заголовков, включая их название (добавлены "Аннотация" и "КОНТАКТНАЯ ИНФОРМАЦИЯ")
heading_pattern = re.compile(r"(\d+(\.\d+)*|Аннотация|КОНТАКТНАЯ ИНФОРМАЦИЯ)")

# Функция для разделения текста на части по заголовкам (включая название)
def split_text_by_headings(text: str, titles: dict):
    documents = []
    matches = list(heading_pattern.finditer(text))
    
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        chapter = matches[i].group(1).strip()  # номер главы или специальный заголовок
        chapter_title = titles.get(chapter, "Неизвестный заголовок")  # заголовок из словаря titles
        
        # Извлечение содержимого между заголовками (включая заголовок)
        content = text[start:end].strip()
        
        # Поиск связанных путей к фотографиям для данной главы
        image_paths = get_files_by_number(chapter)  # используем ранее написанную функцию

        # Создаем объект Document с метаданными
        doc = Document(
            page_content=content[:1000],
            metadata={
                "content":content,
                "chapter": chapter,
                "title": chapter_title,
                "paths": image_paths
            }
        )
        documents.append(doc)
    
    return documents

# Получение файлов по номеру главы (реализуй эту функцию)
def get_files_by_number(number):
    # Здесь функция get_files_by_number уже должна быть реализована
    # для получения путей к фоткам, которые соответствуют главе
    return [f for f in os.listdir("images") if f.startswith(str(number)+'_')]

# Применяем функцию для разделения текста
documents = split_text_by_headings(text_content, titles)
print(len(documents))
# Выводим результат
# count = 10
# for doc in documents:
#     print(f"{doc.metadata['chapter']}, Заголовок: {doc.metadata['title']}")
#     print(f"Пути к фоткам: {doc.metadata['paths']}")
#     print(f"Содержимое:\n{len(doc.page_content), doc.page_content}") 
#     if count==-1:
#         break
#     count -=1
#     print()