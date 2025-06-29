import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
UPLOAD_DIR = BASE_DIR / "uploads"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
LOGS_DIR = BASE_DIR / "logs"

# Создание директорий если они не существуют
for dir_path in [UPLOAD_DIR, VECTOR_STORE_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Модели ИИ
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
LLM_MODEL = os.getenv('LLM_MODEL', 'distilgpt2')  # Используем более легкую модель

# Flask конфигурация
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Пути к файлам
UPLOAD_FOLDER = str(UPLOAD_DIR)
VECTOR_STORE_PATH = str(VECTOR_STORE_DIR)
LOGS_PATH = str(LOGS_DIR)

# Поддерживаемые форматы файлов
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Tesseract OCR (для Linux окружения)
TESSERACT_CMD = '/usr/bin/tesseract'  # Путь к tesseract в Linux

# Настройки чат-бота
MAX_CONTEXT_LENGTH = 512
MAX_RESPONSE_LENGTH = 256
TOP_K_DOCUMENTS = 5
SIMILARITY_THRESHOLD = 0.7

# Redis настройки (для кэширования)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# CORS настройки
CORS_ORIGINS = ['*']  # В production указать конкретные домены

# Rate limiting
RATE_LIMIT_DEFAULT = "100 per hour"
RATE_LIMIT_CHAT = "10 per minute"

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/chatbot.db')