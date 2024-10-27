# app/services/model_loader.py

import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

class ModelLoader:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Используемое устройство для модели: {self.device}")
        
        # Загрузка модели на устройство
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct",
            torch_dtype=torch.float16,  # Используем float16 для экономии памяти
            device_map="auto"
        )
        self.model.to(self.device)
        
        # Загрузка процессора
        self.processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

    def get_model(self):
        return self.model

    def get_processor(self):
        return self.processor
