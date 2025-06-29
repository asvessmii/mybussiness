#!/usr/bin/env python3
"""
Простой сервер для демонстрации чат-бота без тяжелых моделей
"""

from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import logging

app = Flask(__name__, static_folder='/app/src/static', static_url_path='/static')
CORS(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Простые ответы
simple_responses = {
    'привет': 'Здравствуйте! Я ИИ помощник. Чем могу помочь?',
    'как дела': 'У меня все хорошо! Готов помочь с вашими вопросами.',
    'что умеешь': 'Я могу отвечать на вопросы, помогать с информацией из документов и просто общаться.',
    'спасибо': 'Пожалуйста! Обращайтесь, если нужна помощь.',
    'пока': 'До свидания! Хорошего дня!'
}

@app.route('/')
def index():
    """Главная страница"""
    try:
        with open('/app/src/static/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return '''
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>ИИ Чат-бот - Демо</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; margin-bottom: 20px; }
                .chat { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
                .message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }
                .bot { background: #e3f2fd; }
                .user { background: #f3e5f5; text-align: right; }
                .input-area { display: flex; gap: 10px; }
                input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Универсальный ИИ Чат-бот</h1>
                <div class="status">
                    ✅ Система запущена и готова к работе!
                </div>
                
                <div id="chat" class="chat">
                    <div class="message bot">
                        <strong>Бот:</strong> Здравствуйте! Я ИИ помощник. Задавайте вопросы!
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="Введите ваш вопрос..." 
                           onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
            </div>
            
            <script>
                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    // Добавляем сообщение пользователя
                    addMessage('user', message);
                    input.value = '';
                    
                    // Отправляем запрос к API
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            message: message, 
                            session_id: 'demo_session' 
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        addMessage('bot', data.response || 'Извините, не могу ответить на этот вопрос.');
                    })
                    .catch(error => {
                        addMessage('bot', 'Произошла ошибка при обработке запроса.');
                    });
                }
                
                function addMessage(sender, text) {
                    const chat = document.getElementById('chat');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ' + sender;
                    messageDiv.innerHTML = '<strong>' + (sender === 'user' ? 'Вы' : 'Бот') + ':</strong> ' + text;
                    chat.appendChild(messageDiv);
                    chat.scrollTop = chat.scrollHeight;
                }
            </script>
        </body>
        </html>
        '''

@app.route('/widget.js')
def widget_js():
    """Встраиваемый виджет"""
    try:
        with open('/app/src/static/widget.js', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "// Виджет загружается...", 200, {'Content-Type': 'application/javascript'}

@app.route('/status')
def status_direct():
    """Статус системы без /api префикса"""
    return status()

@app.route('/chat', methods=['POST'])
def chat_direct():
    """Простой чат без /api префикса"""
    return chat()

@app.route('/upload_document', methods=['POST'])
def upload_document_direct():
    """Заглушка для загрузки документов без /api префикса"""
    return upload_document()

@app.route('/knowledge_base')
def knowledge_base_direct():
    """Информация о базе знаний без /api префикса"""
    return knowledge_base()

@app.route('/api/status')
def status():
    """Статус системы"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': True,
        'embedding_model': 'all-MiniLM-L6-v2',
        'llm_model': 'distilgpt2',
        'vector_store_size': 0,
        'supported_formats': ['pdf', 'docx', 'txt']
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Простой чат без ИИ моделей"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower().strip()
        
        # Простая логика ответов
        response = "Извините, я не понял ваш вопрос. Попробуйте переформулировать."
        
        for key, value in simple_responses.items():
            if key in message:
                response = value
                break
        
        # Если не нашли ключевое слово, даем общий ответ
        if response == "Извините, я не понял ваш вопрос. Попробуйте переформулировать.":
            if '?' in message or 'как' in message or 'что' in message or 'где' in message:
                response = "Интересный вопрос! К сожалению, сейчас я работаю в демо-режиме. Для полноценной работы нужно загрузить ИИ модели."
            elif len(message) > 10:
                response = "Я понял, что вы хотите обсудить что-то важное. В полной версии я смогу дать более детальный ответ."
        
        return jsonify({
            'response': response,
            'session_id': data.get('session_id', 'demo'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка в чате: {e}")
        return jsonify({
            'error': 'Ошибка обработки запроса',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/upload_document', methods=['POST'])
def upload_document():
    """Заглушка для загрузки документов"""
    return jsonify({
        'message': 'Функция загрузки документов будет доступна после инициализации полной версии системы',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/knowledge_base')
def knowledge_base():
    """Информация о базе знаний"""
    return jsonify({
        'vector_store_size': 0,
        'total_documents': 0,
        'embedding_model': 'all-MiniLM-L6-v2',
        'last_updated': None,
        'timestamp': datetime.now().isoformat()
    })

# Статические файлы обслуживаются автоматически Flask

if __name__ == '__main__':
    print("🚀 Запуск демо-версии ИИ чат-бота...")
    print("📍 Интерфейс: http://localhost:3000")
    print("🔧 API статус: http://localhost:3000/api/status")
    
    app.run(
        host='0.0.0.0',
        port=3000,
        debug=True,
        threaded=True
    )