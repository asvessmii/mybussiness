"""
Система управления проектами чат-ботов
"""

import os
import json
import sqlite3
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

import config
from models.web_scraper import WebScraper, SimpleScraper
from models.chatbot import ChatbotModel
from models.data_processor import DocumentProcessor


class ProjectManager:
    """Менеджер проектов для создания специализированных чат-ботов"""
    
    def __init__(self):
        self.db_path = os.path.join(config.BASE_DIR, 'projects.db')
        self.projects_dir = os.path.join(config.BASE_DIR, 'projects')
        
        # Создаем директории если не существуют
        os.makedirs(self.projects_dir, exist_ok=True)
        
        # Инициализируем базу данных
        self._init_database()
        
        # Кэш для активных чат-ботов
        self.active_chatbots = {}
    
    def _init_database(self):
        """Инициализация базы данных проектов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица проектов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        status TEXT DEFAULT 'created',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        scraping_completed_at TEXT,
                        training_completed_at TEXT,
                        config TEXT,
                        stats TEXT
                    )
                ''')
                
                # Таблица собранных данных
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                ''')
                
                # Таблица сессий чата
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        messages TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                ''')
                
                conn.commit()
                logging.info("База данных проектов инициализирована")
                
        except Exception as e:
            logging.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def create_project(self, name: str, url: str) -> Dict[str, Any]:
        """Создание нового проекта"""
        try:
            project_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Сохраняем в базу данных
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects (id, name, url, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (project_id, name, url, 'created', now, now))
                conn.commit()
            
            # Создаем директорию проекта
            project_dir = os.path.join(self.projects_dir, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            logging.info(f"Создан проект: {name} ({project_id})")
            
            return {
                'id': project_id,
                'name': name,
                'url': url,
                'status': 'created',
                'created_at': now
            }
            
        except Exception as e:
            logging.error(f"Ошибка создания проекта: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о проекте"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, url, status, created_at, updated_at,
                           scraping_completed_at, training_completed_at, config, stats
                    FROM projects WHERE id = ?
                ''', (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'url': row[2],
                        'status': row[3],
                        'created_at': row[4],
                        'updated_at': row[5],
                        'scraping_completed_at': row[6],
                        'training_completed_at': row[7],
                        'config': json.loads(row[8]) if row[8] else {},
                        'stats': json.loads(row[9]) if row[9] else {}
                    }
                
                return None
                
        except Exception as e:
            logging.error(f"Ошибка получения проекта {project_id}: {e}")
            return None
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Получение списка всех проектов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, url, status, created_at, updated_at,
                           scraping_completed_at, training_completed_at, stats
                    FROM projects ORDER BY created_at DESC
                ''')
                
                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        'id': row[0],
                        'name': row[1],
                        'url': row[2],
                        'status': row[3],
                        'created_at': row[4],
                        'updated_at': row[5],
                        'scraping_completed_at': row[6],
                        'training_completed_at': row[7],
                        'stats': json.loads(row[8]) if row[8] else {}
                    })
                
                return projects
                
        except Exception as e:
            logging.error(f"Ошибка получения списка проектов: {e}")
            return []
    
    async def start_scraping(self, project_id: str) -> Dict[str, Any]:
        """Запуск скрапинга для проекта"""
        try:
            project = self.get_project(project_id)
            if not project:
                return {'status': 'error', 'message': 'Проект не найден'}
            
            # Обновляем статус
            self._update_project_status(project_id, 'scraping')
            
            # Запускаем скрапер
            async with WebScraper() as scraper:
                scraping_result = await scraper.scrape_website(
                    project['url'],
                    max_depth=3,
                    max_pages=50
                )
                
                if scraping_result['status'] == 'success':
                    # Сохраняем собранные данные
                    await self._save_scraped_data(project_id, scraping_result['data_collected'])
                    
                    # Обновляем проект
                    self._update_project_status(project_id, 'scraped')
                    self._update_project_field(project_id, 'scraping_completed_at', datetime.now().isoformat())
                    self._update_project_field(project_id, 'stats', json.dumps(scraper.get_scraping_stats()))
                    
                    return {
                        'status': 'success',
                        'message': 'Скрапинг завершен успешно',
                        'stats': scraper.get_scraping_stats()
                    }
                else:
                    self._update_project_status(project_id, 'scraping_failed')
                    return {
                        'status': 'error',
                        'message': f'Ошибка скрапинга: {scraping_result.get("error", "Unknown error")}'
                    }
                    
        except Exception as e:
            logging.error(f"Ошибка скрапинга проекта {project_id}: {e}")
            self._update_project_status(project_id, 'scraping_failed')
            return {'status': 'error', 'message': str(e)}
    
    async def _save_scraped_data(self, project_id: str, data_items: List[Dict[str, Any]]):
        """Сохранение собранных данных в базу"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for item in data_items:
                    cursor.execute('''
                        INSERT INTO project_data (project_id, data_type, content, source, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        project_id,
                        item.get('type', 'unknown'),
                        item.get('content', ''),
                        item.get('source', ''),
                        json.dumps({k: v for k, v in item.items() if k not in ['type', 'content', 'source']}),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                logging.info(f"Сохранено {len(data_items)} элементов данных для проекта {project_id}")
                
        except Exception as e:
            logging.error(f"Ошибка сохранения данных проекта {project_id}: {e}")
            raise
    
    def start_training(self, project_id: str) -> Dict[str, Any]:
        """Запуск обучения модели для проекта"""
        try:
            project = self.get_project(project_id)
            if not project:
                return {'status': 'error', 'message': 'Проект не найден'}
            
            if project['status'] != 'scraped':
                return {'status': 'error', 'message': 'Проект должен быть сначала обработан скрапером'}
            
            # Обновляем статус
            self._update_project_status(project_id, 'training')
            
            # Получаем данные проекта
            project_data = self._get_project_data(project_id)
            
            if not project_data:
                self._update_project_status(project_id, 'training_failed')
                return {'status': 'error', 'message': 'Нет данных для обучения'}
            
            # Создаем специализированный чат-бот
            chatbot = ChatbotModel()
            
            # Обучаем на собранных данных
            total_text = ""
            for item in project_data:
                total_text += f"\n\n{item['content']}"
            
            # Обновляем базу знаний
            chatbot.update_knowledge_base(total_text, f"project_{project_id}")
            
            # Сохраняем модель
            self._save_project_model(project_id, chatbot)
            
            # Обновляем статус
            self._update_project_status(project_id, 'ready')
            self._update_project_field(project_id, 'training_completed_at', datetime.now().isoformat())
            
            return {
                'status': 'success',
                'message': 'Обучение завершено успешно',
                'model_stats': {
                    'vector_store_size': chatbot.get_vector_store_size(),
                    'training_data_size': len(total_text)
                }
            }
            
        except Exception as e:
            logging.error(f"Ошибка обучения проекта {project_id}: {e}")
            self._update_project_status(project_id, 'training_failed')
            return {'status': 'error', 'message': str(e)}
    
    def _get_project_data(self, project_id: str) -> List[Dict[str, Any]]:
        """Получение данных проекта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT data_type, content, source, metadata, created_at
                    FROM project_data WHERE project_id = ?
                    ORDER BY created_at
                ''', (project_id,))
                
                data = []
                for row in cursor.fetchall():
                    data.append({
                        'type': row[0],
                        'content': row[1],
                        'source': row[2],
                        'metadata': json.loads(row[3]) if row[3] else {},
                        'created_at': row[4]
                    })
                
                return data
                
        except Exception as e:
            logging.error(f"Ошибка получения данных проекта {project_id}: {e}")
            return []
    
    def _save_project_model(self, project_id: str, chatbot: ChatbotModel):
        """Сохранение модели проекта"""
        try:
            project_dir = os.path.join(self.projects_dir, project_id)
            
            # Сохраняем векторное хранилище в директорию проекта
            import shutil
            if os.path.exists(config.VECTOR_STORE_PATH):
                project_vector_store = os.path.join(project_dir, 'vector_store')
                if os.path.exists(project_vector_store):
                    shutil.rmtree(project_vector_store)
                shutil.copytree(config.VECTOR_STORE_PATH, project_vector_store)
            
            # Сохраняем метаданные модели
            model_metadata = {
                'project_id': project_id,
                'created_at': datetime.now().isoformat(),
                'vector_store_size': chatbot.get_vector_store_size(),
                'embedding_model': config.EMBEDDING_MODEL,
                'llm_model': config.LLM_MODEL
            }
            
            with open(os.path.join(project_dir, 'model_metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(model_metadata, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Модель проекта {project_id} сохранена")
            
        except Exception as e:
            logging.error(f"Ошибка сохранения модели проекта {project_id}: {e}")
            raise
    
    def get_project_chatbot(self, project_id: str) -> Optional[ChatbotModel]:
        """Получение чат-бота проекта"""
        try:
            # Проверяем кэш
            if project_id in self.active_chatbots:
                return self.active_chatbots[project_id]
            
            project = self.get_project(project_id)
            if not project or project['status'] != 'ready':
                return None
            
            # Загружаем модель
            project_dir = os.path.join(self.projects_dir, project_id)
            project_vector_store = os.path.join(project_dir, 'vector_store')
            
            if not os.path.exists(project_vector_store):
                return None
            
            # Создаем чат-бот и загружаем данные
            chatbot = ChatbotModel()
            
            # Временно подменяем путь к векторному хранилищу
            original_path = config.VECTOR_STORE_PATH
            config.VECTOR_STORE_PATH = project_vector_store
            
            try:
                chatbot._initialize_vector_store()
            finally:
                config.VECTOR_STORE_PATH = original_path
            
            # Кэшируем
            self.active_chatbots[project_id] = chatbot
            
            return chatbot
            
        except Exception as e:
            logging.error(f"Ошибка загрузки чат-бота проекта {project_id}: {e}")
            return None
    
    def chat_with_project(self, project_id: str, message: str, session_id: str) -> Dict[str, Any]:
        """Чат с проектным чат-ботом"""
        try:
            chatbot = self.get_project_chatbot(project_id)
            if not chatbot:
                return {
                    'status': 'error',
                    'message': 'Чат-бот проекта не доступен'
                }
            
            # Генерируем ответ
            response = chatbot.generate_response(message, session_id)
            
            # Сохраняем сессию
            self._save_chat_session(project_id, session_id, message, response)
            
            return {
                'status': 'success',
                'response': response,
                'session_id': session_id
            }
            
        except Exception as e:
            logging.error(f"Ошибка чата с проектом {project_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _save_chat_session(self, project_id: str, session_id: str, user_message: str, bot_response: str):
        """Сохранение сессии чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем существующую сессию
                cursor.execute('SELECT messages FROM chat_sessions WHERE id = ?', (session_id,))
                row = cursor.fetchone()
                
                if row:
                    # Обновляем существующую сессию
                    messages = json.loads(row[0])
                    messages.append({
                        'user': user_message,
                        'bot': bot_response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    cursor.execute('''
                        UPDATE chat_sessions SET messages = ?, updated_at = ?
                        WHERE id = ?
                    ''', (json.dumps(messages), datetime.now().isoformat(), session_id))
                else:
                    # Создаем новую сессию
                    messages = [{
                        'user': user_message,
                        'bot': bot_response,
                        'timestamp': datetime.now().isoformat()
                    }]
                    
                    cursor.execute('''
                        INSERT INTO chat_sessions (id, project_id, messages, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        project_id,
                        json.dumps(messages),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Ошибка сохранения сессии чата: {e}")
    
    def generate_integration_code(self, project_id: str) -> Dict[str, Any]:
        """Генерация кода для интеграции"""
        try:
            project = self.get_project(project_id)
            if not project or project['status'] != 'ready':
                return {
                    'status': 'error',
                    'message': 'Проект не готов для генерации кода'
                }
            
            # Генерируем код
            integration_code = self._generate_chatbot_code(project)
            
            return {
                'status': 'success',
                'code': integration_code,
                'project_name': project['name']
            }
            
        except Exception as e:
            logging.error(f"Ошибка генерации кода для проекта {project_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _generate_chatbot_code(self, project: Dict[str, Any]) -> Dict[str, str]:
        """Генерация кода чат-бота"""
        project_id = project['id']
        project_name = project['name']
        
        # HTML код виджета
        html_code = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Чат-бот {project_name}</title>
    <style>
        .chatbot-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            z-index: 1000;
        }}
        .chatbot-header {{
            background: #007bff;
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
        }}
        .chatbot-messages {{
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .message {{
            max-width: 80%;
            padding: 8px 12px;
            border-radius: 10px;
            word-wrap: break-word;
        }}
        .user-message {{
            background: #007bff;
            color: white;
            align-self: flex-end;
        }}
        .bot-message {{
            background: #f1f1f1;
            color: #333;
            align-self: flex-start;
        }}
        .chatbot-input {{
            display: flex;
            padding: 10px;
            border-top: 1px solid #ddd;
        }}
        .chatbot-input input {{
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            outline: none;
        }}
        .chatbot-input button {{
            margin-left: 10px;
            padding: 10px 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .chatbot-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
        }}
    </style>
</head>
<body>
    <button class="chatbot-toggle" onclick="toggleChatbot()">💬</button>
    
    <div class="chatbot-container" id="chatbot" style="display: none;">
        <div class="chatbot-header">
            Чат-бот {project_name}
            <button onclick="toggleChatbot()" style="float: right; background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
        </div>
        <div class="chatbot-messages" id="messages">
            <div class="message bot-message">
                Привет! Я помощник {project_name}. Чем могу помочь?
            </div>
        </div>
        <div class="chatbot-input">
            <input type="text" id="messageInput" placeholder="Введите ваш вопрос..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Отправить</button>
        </div>
    </div>

    <script>
        const API_URL = 'YOUR_API_URL_HERE';
        const PROJECT_ID = '{project_id}';
        let sessionId = generateSessionId();

        function generateSessionId() {{
            return 'session_' + Math.random().toString(36).substr(2, 9);
        }}

        function toggleChatbot() {{
            const chatbot = document.getElementById('chatbot');
            const toggle = document.querySelector('.chatbot-toggle');
            
            if (chatbot.style.display === 'none') {{
                chatbot.style.display = 'flex';
                toggle.style.display = 'none';
            }} else {{
                chatbot.style.display = 'none';
                toggle.style.display = 'block';
            }}
        }}

        function handleKeyPress(event) {{
            if (event.key === 'Enter') {{
                sendMessage();
            }}
        }}

        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Добавляем сообщение пользователя
            addMessage(message, 'user');
            input.value = '';
            
            // Отправляем запрос к API
            try {{
                const response = await fetch(`${{API_URL}}/api/projects/${{PROJECT_ID}}/chat`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        message: message,
                        session_id: sessionId
                    }})
                }});
                
                const data = await response.json();
                
                if (data.status === 'success') {{
                    addMessage(data.response, 'bot');
                }} else {{
                    addMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'bot');
                }}
            }} catch (error) {{
                console.error('Ошибка:', error);
                addMessage('Извините, произошла ошибка соединения.', 'bot');
            }}
        }}

        function addMessage(text, sender) {{
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{sender}}-message`;
            messageDiv.textContent = text;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }}
    </script>
</body>
</html>'''

        # JavaScript код для встраивания
        js_code = f'''// Встраиваемый чат-бот для {project_name}
(function() {{
    const API_URL = 'YOUR_API_URL_HERE';
    const PROJECT_ID = '{project_id}';
    let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

    // CSS стили
    const styles = `
        .embedded-chatbot {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            z-index: 10000;
            font-family: Arial, sans-serif;
        }}
        /* Остальные стили аналогично HTML версии */
    `;

    // Добавляем стили
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);

    // Создаем HTML структуру
    const chatbotHTML = `
        <button class="chatbot-toggle" onclick="window.toggleEmbeddedChatbot()">💬</button>
        <div class="embedded-chatbot" id="embeddedChatbot">
            <!-- Структура чат-бота -->
        </div>
    `;

    // Добавляем в DOM
    document.body.insertAdjacentHTML('beforeend', chatbotHTML);

    // Глобальные функции
    window.toggleEmbeddedChatbot = function() {{
        // Логика переключения
    }};

    window.sendEmbeddedMessage = async function(message) {{
        // Логика отправки сообщения
    }};
}})();'''

        # Python код для API
        python_code = f'''# API для чат-бота {project_name}
# Требует установки: pip install flask flask-cors

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Здесь должна быть ваша логика чат-бота
# Замените на реальную реализацию

@app.route('/api/projects/{project_id}/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        # Здесь должна быть логика обработки сообщения
        # Замените на реальную реализацию
        response = process_message(message, session_id)
        
        return jsonify({{
            'status': 'success',
            'response': response,
            'session_id': session_id
        }})
        
    except Exception as e:
        return jsonify({{
            'status': 'error',
            'message': str(e)
        }}), 500

def process_message(message, session_id):
    # Здесь должна быть ваша логика обработки
    # Подключите модель и верните ответ
    return f"Получено сообщение: {{message}}"

if __name__ == '__main__':
    app.run(debug=True)
'''

        return {
            'html': html_code,
            'javascript': js_code,
            'python': python_code,
            'readme': f'''# Чат-бот для {project_name}

## Установка и использование

### Вариант 1: HTML страница
Сохраните HTML код в файл и откройте в браузере.
Не забудьте заменить YOUR_API_URL_HERE на реальный URL вашего API.

### Вариант 2: Встраиваемый JavaScript
Добавьте JavaScript код на вашу страницу.

### Вариант 3: Python API
Запустите Python код как отдельный сервис.

## Настройка
1. Замените YOUR_API_URL_HERE на реальный URL
2. Убедитесь, что API доступен по указанному адресу
3. Настройте CORS если необходимо

## Поддержка
Чат-бот обучен на данных с {project['url']}
'''
        }
    
    def _update_project_status(self, project_id: str, status: str):
        """Обновление статуса проекта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE projects SET status = ?, updated_at = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), project_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка обновления статуса проекта {project_id}: {e}")
    
    def _update_project_field(self, project_id: str, field: str, value: str):
        """Обновление поля проекта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE projects SET {field} = ?, updated_at = ?
                    WHERE id = ?
                ''', (value, datetime.now().isoformat(), project_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка обновления поля {field} проекта {project_id}: {e}")
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Удаление проекта"""
        try:
            # Удаляем из базы данных
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM chat_sessions WHERE project_id = ?', (project_id,))
                cursor.execute('DELETE FROM project_data WHERE project_id = ?', (project_id,))
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                conn.commit()
            
            # Удаляем директорию проекта
            import shutil
            project_dir = os.path.join(self.projects_dir, project_id)
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            # Удаляем из кэша
            if project_id in self.active_chatbots:
                del self.active_chatbots[project_id]
            
            return {'status': 'success', 'message': 'Проект успешно удален'}
            
        except Exception as e:
            logging.error(f"Ошибка удаления проекта {project_id}: {e}")
            return {'status': 'error', 'message': str(e)}