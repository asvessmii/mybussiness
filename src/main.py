#!/usr/bin/env python3
"""
Универсальный ИИ Чат-бот
Основная точка входа Flask приложения
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template_string
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import datetime

import config
from routes.chatbot import chatbot_bp
from models.chatbot import ChatbotModel

def create_app():
    """Создание и настройка Flask приложения"""
    app = Flask(__name__, static_folder='static')
    
    # Конфигурация
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    
    # CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[config.RATE_LIMIT_DEFAULT]
    )
    
    # Настройка логирования
    setup_logging()
    
    # Регистрация blueprint'ов
    app.register_blueprint(chatbot_bp, url_prefix='/api')
    
    # Главная страница
    @app.route('/')
    def index():
        """Главная страница с веб-интерфейсом"""
        try:
            with open(os.path.join(app.static_folder, 'index.html'), 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ИИ Чат-бот</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>Универсальный ИИ Чат-бот</h1>
                <p>Система запускается... Интерфейс будет доступен после полной инициализации.</p>
                <p><a href="/api/status">Проверить статус системы</a></p>
            </body>
            </html>
            """)
    
    # Статические файлы
    @app.route('/widget.js')
    def widget_js():
        """Встраиваемый JavaScript виджет"""
        try:
            with open(os.path.join(app.static_folder, 'widget.js'), 'r', encoding='utf-8') as f:
                response = app.response_class(
                    f.read(),
                    mimetype='application/javascript'
                )
                return response
        except FileNotFoundError:
            return "// Виджет загружается...", 200, {'Content-Type': 'application/javascript'}
    
    return app

def setup_logging():
    """Настройка системы логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Создание директории для логов
    config.LOGS_DIR.mkdir(exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(config.LOGS_DIR / 'app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Отдельный лог для Flask
    flask_logger = logging.getLogger('werkzeug')
    flask_handler = logging.FileHandler(config.LOGS_DIR / 'flask.log', encoding='utf-8')
    flask_handler.setFormatter(logging.Formatter(log_format))
    flask_logger.addHandler(flask_handler)

if __name__ == '__main__':
    app = create_app()
    
    logging.info("Запуск универсального ИИ чат-бота...")
    logging.info(f"Режим: {config.FLASK_ENV}")
    logging.info(f"Модель эмбеддингов: {config.EMBEDDING_MODEL}")
    logging.info(f"Языковая модель: {config.LLM_MODEL}")
    
    # Запуск приложения
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(config.FLASK_ENV == 'development'),
        threaded=True
    )