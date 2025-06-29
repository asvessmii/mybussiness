FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/
COPY uploads/ ./uploads/
COPY vector_store/ ./vector_store/

# Создание директорий для логов и данных
RUN mkdir -p logs uploads vector_store

# Создание пользователя для безопасности
RUN useradd -m -u 1000 chatbot && chown -R chatbot:chatbot /app
USER chatbot

# Открытие порта
EXPOSE 5000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Команда запуска
CMD ["python", "src/main.py"]

