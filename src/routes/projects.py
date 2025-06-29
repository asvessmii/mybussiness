"""
API маршруты для управления проектами
"""

import os
import uuid
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

import config
from models.project_manager import ProjectManager

# Создание Blueprint
projects_bp = Blueprint('projects', __name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Глобальный менеджер проектов
project_manager = None

def get_project_manager():
    """Получение экземпляра менеджера проектов"""
    global project_manager
    if project_manager is None:
        project_manager = ProjectManager()
    return project_manager

@projects_bp.route('/projects', methods=['GET'])
def get_projects():
    """Получение списка всех проектов"""
    try:
        manager = get_project_manager()
        projects = manager.get_all_projects()
        
        return jsonify({
            'status': 'success',
            'projects': projects,
            'total': len(projects),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка получения проектов: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects', methods=['POST'])
@limiter.limit("5 per minute")
def create_project():
    """Создание нового проекта"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'url' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Название и URL проекта обязательны',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        name = data['name'].strip()
        url = data['url'].strip()
        
        if not name or not url:
            return jsonify({
                'status': 'error',
                'message': 'Название и URL не могут быть пустыми',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Проверяем URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        manager = get_project_manager()
        project = manager.create_project(name, url)
        
        logging.info(f"Создан проект: {name}")
        
        return jsonify({
            'status': 'success',
            'message': 'Проект создан успешно',
            'project': project,
            'timestamp': datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logging.error(f"Ошибка создания проекта: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Получение информации о проекте"""
    try:
        manager = get_project_manager()
        project = manager.get_project(project_id)
        
        if not project:
            return jsonify({
                'status': 'error',
                'message': 'Проект не найден',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        return jsonify({
            'status': 'success',
            'project': project,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка получения проекта {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>/scrape', methods=['POST'])
@limiter.limit("2 per minute")
def start_scraping(project_id):
    """Запуск скрапинга проекта"""
    try:
        manager = get_project_manager()
        project = manager.get_project(project_id)
        
        if not project:
            return jsonify({
                'status': 'error',
                'message': 'Проект не найден',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        if project['status'] in ['scraping', 'training']:
            return jsonify({
                'status': 'error',
                'message': 'Проект уже обрабатывается',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Запускаем скрапинг асинхронно
        async def run_scraping():
            return await manager.start_scraping(project_id)
        
        # Поскольку Flask синхронный, запускаем в новом event loop
        import threading
        
        def scraping_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_scraping())
                logging.info(f"Скрапинг проекта {project_id} завершен: {result}")
            except Exception as e:
                logging.error(f"Ошибка в потоке скрапинга: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=scraping_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Скрапинг запущен',
            'project_id': project_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка запуска скрапинга {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>/train', methods=['POST'])
@limiter.limit("2 per minute")
def start_training(project_id):
    """Запуск обучения модели проекта"""
    try:
        manager = get_project_manager()
        
        # Запускаем обучение в отдельном потоке
        def training_thread():
            try:
                result = manager.start_training(project_id)
                logging.info(f"Обучение проекта {project_id} завершено: {result}")
            except Exception as e:
                logging.error(f"Ошибка в потоке обучения: {e}")
        
        thread = threading.Thread(target=training_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Обучение запущено',
            'project_id': project_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка запуска обучения {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat_with_project(project_id):
    """Чат с проектным чат-ботом"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Сообщение обязательно',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        message = data['message'].strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Сообщение не может быть пустым',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        manager = get_project_manager()
        result = manager.chat_with_project(project_id, message, session_id)
        
        if result['status'] == 'success':
            logging.info(f"Chat project {project_id} - Session: {session_id}, Message: {message[:50]}...")
        
        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        logging.error(f"Ошибка чата с проектом {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>/generate-code', methods=['POST'])
@limiter.limit("10 per minute")
def generate_integration_code(project_id):
    """Генерация кода для интеграции"""
    try:
        manager = get_project_manager()
        result = manager.generate_integration_code(project_id)
        
        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        logging.error(f"Ошибка генерации кода для проекта {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
@limiter.limit("5 per minute")
def delete_project(project_id):
    """Удаление проекта"""
    try:
        manager = get_project_manager()
        result = manager.delete_project(project_id)
        
        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        logging.error(f"Ошибка удаления проекта {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.route('/projects/<project_id>/status', methods=['GET'])
def get_project_status(project_id):
    """Получение статуса проекта"""
    try:
        manager = get_project_manager()
        project = manager.get_project(project_id)
        
        if not project:
            return jsonify({
                'status': 'error',
                'message': 'Проект не найден',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Дополнительная информация о статусе
        status_info = {
            'project_id': project_id,
            'status': project['status'],
            'created_at': project['created_at'],
            'updated_at': project['updated_at'],
            'scraping_completed_at': project.get('scraping_completed_at'),
            'training_completed_at': project.get('training_completed_at'),
            'stats': project.get('stats', {}),
            'is_ready': project['status'] == 'ready'
        }
        
        # Если проект готов, добавляем информацию о модели
        if project['status'] == 'ready':
            chatbot = manager.get_project_chatbot(project_id)
            if chatbot:
                status_info['model_info'] = {
                    'vector_store_size': chatbot.get_vector_store_size(),
                    'documents_count': len(chatbot.get_document_list())
                }
        
        return jsonify({
            'status': 'success',
            'project_status': status_info,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка получения статуса проекта {project_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@projects_bp.errorhandler(429)
def ratelimit_handler(e):
    """Обработка превышения лимита запросов"""
    return jsonify({
        'status': 'error',
        'message': 'Превышен лимит запросов',
        'description': str(e.description),
        'timestamp': datetime.now().isoformat()
    }), 429