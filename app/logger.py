import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Создаем директорию для логов, если она не существует
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Настраиваем RotatingFileHandler
    file_handler = RotatingFileHandler(
        'logs/app.log', maxBytes=10485760, backupCount=5)
    file_handler.setLevel(logging.INFO)

    # Настраиваем ConsoleHandler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Создаем форматтер и добавляем его к обработчикам
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
