"""
API маршруты для чат-бота
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import logging

import config
from models.chatbot import ChatbotModel
from models.data_processor import DocumentProcessor

# Создание Blueprint
chatbot_bp = Blueprint('chatbot', __name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Глобальные переменные для моделей
chatbot_model = None
document_processor = None

def get_chatbot_model():
    """Получение экземпляра модели чат-бота"""
    global chatbot_model
    if chatbot_model is None:
        chatbot_model = ChatbotModel()
    return chatbot_model

def get_document_processor():
    """Получение экземпляра процессора документов"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor

def allowed_file(filename):
    """Проверка разрешенных форматов файлов"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@chatbot_bp.route('/status', methods=['GET'])
def status():
    """Проверка статуса системы"""
    try:
        model = get_chatbot_model()
        
        # Базовая статистика
        stats = {
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'models_loaded': model.is_initialized(),
            'embedding_model': config.EMBEDDING_MODEL,
            'llm_model': config.LLM_MODEL,
            'vector_store_size': model.get_vector_store_size(),
            'supported_formats': list(config.ALLOWED_EXTENSIONS)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging.error(f"Ошибка получения статуса: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@chatbot_bp.route('/chat', methods=['POST'])
@limiter.limit(config.RATE_LIMIT_CHAT)
def chat():
    """Основной endpoint для чата"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Сообщение обязательно',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        message = data['message'].strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({
                'error': 'Сообщение не может быть пустым',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Получение ответа от чат-бота
        model = get_chatbot_model()
        response = model.generate_response(message, session_id)
        
        # Логирование запроса
        logging.info(f"Chat request - Session: {session_id}, Message: {message[:50]}...")
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка обработки чата: {e}")
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'timestamp': datetime.now().isoformat()
        }), 500

@chatbot_bp.route('/upload_document', methods=['POST'])
@limiter.limit("5 per minute")
def upload_document():
    """Загрузка документа в базу знаний"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'Файл не найден в запросе',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'Файл не выбран',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if file and allowed_file(file.filename):
            # Безопасное имя файла
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(config.UPLOAD_FOLDER, unique_filename)
            
            # Сохранение файла
            file.save(filepath)
            
            # Обработка документа
            processor = get_document_processor()
            result = processor.process_document(filepath)
            
            if result['success']:
                # Обновление векторного хранилища
                model = get_chatbot_model()
                model.update_knowledge_base(result['text'], unique_filename)
                
                logging.info(f"Документ загружен: {filename}")
                
                return jsonify({
                    'message': 'Документ успешно загружен и обработан',
                    'filename': filename,
                    'file_id': unique_filename,
                    'pages_processed': result.get('pages_processed', 1),
                    'timestamp': datetime.now().isoformat()
                }), 200
            else:
                # Удаление файла в случае ошибки обработки
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify({
                    'error': f'Ошибка обработки документа: {result["error"]}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        else:
            return jsonify({
                'error': f'Неподдерживаемый формат файла. Поддерживаются: {", ".join(config.ALLOWED_EXTENSIONS)}',
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logging.error(f"Ошибка загрузки документа: {e}")
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'timestamp': datetime.now().isoformat()
        }), 500

@chatbot_bp.route('/knowledge_base', methods=['GET'])
def knowledge_base_info():
    """Информация о базе знаний"""
    try:
        model = get_chatbot_model()
        
        info = {
            'vector_store_size': model.get_vector_store_size(),
            'total_documents': len(model.get_document_list()),
            'embedding_model': config.EMBEDDING_MODEL,
            'last_updated': model.get_last_update_time(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        logging.error(f"Ошибка получения информации о базе знаний: {e}")
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'timestamp': datetime.now().isoformat()
        }), 500

@chatbot_bp.route('/search', methods=['POST'])
@limiter.limit("20 per minute")
def search_knowledge_base():
    """Поиск в базе знаний"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Запрос обязателен',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        query = data['query'].strip()
        top_k = data.get('top_k', config.TOP_K_DOCUMENTS)
        
        if not query:
            return jsonify({
                'error': 'Запрос не может быть пустым',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Поиск в базе знаний
        model = get_chatbot_model()
        results = model.search_knowledge_base(query, top_k)
        
        return jsonify({
            'results': results,
            'query': query,
            'total_found': len(results),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Ошибка поиска в базе знаний: {e}")
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'timestamp': datetime.now().isoformat()
        }), 500

@chatbot_bp.errorhandler(429)
def ratelimit_handler(e):
    """Обработка превышения лимита запросов"""
    return jsonify({
        'error': 'Превышен лимит запросов',
        'message': str(e.description),
        'timestamp': datetime.now().isoformat()
    }), 429