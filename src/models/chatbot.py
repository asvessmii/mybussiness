"""
Основная модель чат-бота с поддержкой RAG (Retrieval-Augmented Generation)
"""

import os
import json
import pickle
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

import torch
from transformers import (
    AutoTokenizer, AutoModel, 
    AutoModelForCausalLM, 
    pipeline
)
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.metrics.pairwise import cosine_similarity

import config

class ChatbotModel:
    """Основная модель чат-бота с поддержкой RAG"""
    
    def __init__(self):
        self.embedding_model = None
        self.llm_model = None
        self.llm_tokenizer = None
        self.vector_store = None
        self.document_store = {}
        self.index_to_doc_mapping = {}
        self.session_contexts = {}
        self.initialized = False
        self.last_update = None
        
        # Инициализация при создании экземпляра
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация ИИ моделей"""
        try:
            logging.info("Загрузка модели эмбеддингов...")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            
            logging.info("Загрузка языковой модели...")
            self.llm_tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL)
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                config.LLM_MODEL,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Добавляем pad_token если его нет
            if self.llm_tokenizer.pad_token is None:
                self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
            
            # Инициализация векторного хранилища
            self._initialize_vector_store()
            
            self.initialized = True
            logging.info("Модели успешно инициализированы")
            
        except Exception as e:
            logging.error(f"Ошибка инициализации моделей: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Инициализация или загрузка векторного хранилища"""
        vector_store_path = os.path.join(config.VECTOR_STORE_PATH, 'faiss_index.bin')
        document_store_path = os.path.join(config.VECTOR_STORE_PATH, 'document_store.pkl')
        mapping_path = os.path.join(config.VECTOR_STORE_PATH, 'index_mapping.pkl')
        
        try:
            if os.path.exists(vector_store_path):
                # Загрузка существующего хранилища
                self.vector_store = faiss.read_index(vector_store_path)
                
                with open(document_store_path, 'rb') as f:
                    self.document_store = pickle.load(f)
                
                with open(mapping_path, 'rb') as f:
                    self.index_to_doc_mapping = pickle.load(f)
                
                logging.info(f"Загружено векторное хранилище: {self.vector_store.ntotal} документов")
            else:
                # Создание нового хранилища
                embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                self.vector_store = faiss.IndexFlatIP(embedding_dim)  # Inner Product для косинусного сходства
                logging.info("Создано новое векторное хранилище")
                
        except Exception as e:
            logging.error(f"Ошибка инициализации векторного хранилища: {e}")
            # Создание нового хранилища в случае ошибки
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.vector_store = faiss.IndexFlatIP(embedding_dim)
    
    def is_initialized(self) -> bool:
        """Проверка инициализации моделей"""
        return self.initialized
    
    def generate_response(self, message: str, session_id: str) -> str:
        """Генерация ответа на основе сообщения пользователя"""
        try:
            if not self.initialized:
                return "Система инициализируется, попробуйте позже."
            
            # Поиск релевантных документов
            relevant_docs = self.search_knowledge_base(message, config.TOP_K_DOCUMENTS)
            
            # Формирование контекста
            context = self._build_context(relevant_docs, message, session_id)
            
            # Генерация ответа
            response = self._generate_llm_response(context, message)
            
            # Обновление контекста сессии
            self._update_session_context(session_id, message, response)
            
            return response
            
        except Exception as e:
            logging.error(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."
    
    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Поиск релевантных документов в базе знаний"""
        try:
            if self.vector_store is None or self.vector_store.ntotal == 0:
                return []
            
            # Создание эмбеддинга запроса
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding.astype('float32')
            
            # Нормализация для косинусного сходства
            faiss.normalize_L2(query_embedding)
            
            # Поиск в векторном хранилище
            scores, indices = self.vector_store.search(query_embedding, min(top_k, self.vector_store.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx in self.index_to_doc_mapping and score > config.SIMILARITY_THRESHOLD:
                    doc_id = self.index_to_doc_mapping[idx]
                    if doc_id in self.document_store:
                        doc_data = self.document_store[doc_id]
                        results.append({
                            'text': doc_data['text'],
                            'filename': doc_data.get('filename', 'Unknown'),
                            'similarity': float(score),
                            'chunk_id': doc_data.get('chunk_id', 0)
                        })
            
            return results
            
        except Exception as e:
            logging.error(f"Ошибка поиска в базе знаний: {e}")
            return []
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]], query: str, session_id: str) -> str:
        """Формирование контекста для генерации ответа"""
        context_parts = []
        
        # Добавление релевантных документов
        if relevant_docs:
            context_parts.append("Релевантная информация:")
            for doc in relevant_docs[:3]:  # Используем только топ-3 документа
                context_parts.append(f"- {doc['text'][:200]}...")
        
        # Добавление истории сессии (последние 2 сообщения)
        if session_id in self.session_contexts:
            recent_context = self.session_contexts[session_id][-2:]
            if recent_context:
                context_parts.append("\nПредыдущий контекст:")
                for ctx in recent_context:
                    context_parts.append(f"Пользователь: {ctx['user']}")
                    context_parts.append(f"Бот: {ctx['bot']}")
        
        context_parts.append(f"\nВопрос пользователя: {query}")
        context_parts.append("Ответ:")
        
        return "\n".join(context_parts)
    
    def _generate_llm_response(self, context: str, query: str) -> str:
        """Генерация ответа с помощью языковой модели"""
        try:
            # Ограничение длины контекста
            max_context_length = config.MAX_CONTEXT_LENGTH - config.MAX_RESPONSE_LENGTH
            
            # Токенизация контекста
            inputs = self.llm_tokenizer.encode(
                context, 
                truncation=True, 
                max_length=max_context_length,
                return_tensors='pt'
            )
            
            # Генерация ответа
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    inputs,
                    max_new_tokens=config.MAX_RESPONSE_LENGTH,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.llm_tokenizer.eos_token_id,
                    eos_token_id=self.llm_tokenizer.eos_token_id
                )
            
            # Декодирование ответа
            response = self.llm_tokenizer.decode(
                outputs[0][len(inputs[0]):], 
                skip_special_tokens=True
            ).strip()
            
            # Если модель не сгенерировала ответ, используем простую логику
            if not response or len(response) < 10:
                response = self._generate_simple_response(query)
            
            return response
            
        except Exception as e:
            logging.error(f"Ошибка генерации LLM ответа: {e}")
            return self._generate_simple_response(query)
    
    def _generate_simple_response(self, query: str) -> str:
        """Простая генерация ответа на основе ключевых слов"""
        query_lower = query.lower()
        
        # Приветствия
        greetings = ['привет', 'здравствуй', 'добро пожаловать', 'hello', 'hi']
        if any(word in query_lower for word in greetings):
            return "Здравствуйте! Я ИИ помощник. Чем могу помочь?"
        
        # Вопросы о помощи
        help_words = ['помощь', 'помоги', 'что умеешь', 'возможности']
        if any(word in query_lower for word in help_words):
            return "Я могу помочь найти информацию в загруженных документах, ответить на вопросы и предоставить релевантную информацию. Просто задайте свой вопрос!"
        
        # Благодарности
        thanks = ['спасибо', 'благодарю', 'thank']
        if any(word in query_lower for word in thanks):
            return "Пожалуйста! Рад помочь. Если у вас есть еще вопросы, обращайтесь!"
        
        # Общий ответ
        return "Я понял ваш вопрос, но не смог найти точную информацию в базе знаний. Попробуйте переформулировать вопрос или загрузить дополнительные документы."
    
    def _update_session_context(self, session_id: str, user_message: str, bot_response: str):
        """Обновление контекста сессии"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = []
        
        self.session_contexts[session_id].append({
            'user': user_message,
            'bot': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничение размера контекста (последние 10 обменов)
        if len(self.session_contexts[session_id]) > 10:
            self.session_contexts[session_id] = self.session_contexts[session_id][-10:]
    
    def update_knowledge_base(self, text: str, filename: str):
        """Обновление базы знаний новым документом"""
        try:
            # Разбиение текста на чанки
            chunks = self._split_text_into_chunks(text)
            
            for i, chunk in enumerate(chunks):
                # Создание эмбеддинга
                embedding = self.embedding_model.encode([chunk])
                embedding = embedding.astype('float32')
                
                # Нормализация для косинусного сходства
                faiss.normalize_L2(embedding)
                
                # Добавление в векторное хранилище
                current_index = self.vector_store.ntotal
                self.vector_store.add(embedding)
                
                # Создание уникального ID документа
                doc_id = f"{filename}_{i}"
                
                # Сохранение документа
                self.document_store[doc_id] = {
                    'text': chunk,
                    'filename': filename,
                    'chunk_id': i,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Маппинг индекса на документ
                self.index_to_doc_mapping[current_index] = doc_id
            
            # Сохранение обновленного хранилища
            self._save_vector_store()
            self.last_update = datetime.now()
            
            logging.info(f"Добавлено {len(chunks)} чанков из документа {filename}")
            
        except Exception as e:
            logging.error(f"Ошибка обновления базы знаний: {e}")
            raise
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """Разбиение текста на чанки для лучшего поиска"""
        # Простое разбиение по предложениям
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _save_vector_store(self):
        """Сохранение векторного хранилища"""
        try:
            vector_store_path = os.path.join(config.VECTOR_STORE_PATH, 'faiss_index.bin')
            document_store_path = os.path.join(config.VECTOR_STORE_PATH, 'document_store.pkl')
            mapping_path = os.path.join(config.VECTOR_STORE_PATH, 'index_mapping.pkl')
            
            # Сохранение FAISS индекса
            faiss.write_index(self.vector_store, vector_store_path)
            
            # Сохранение хранилища документов
            with open(document_store_path, 'wb') as f:
                pickle.dump(self.document_store, f)
            
            # Сохранение маппинга
            with open(mapping_path, 'wb') as f:
                pickle.dump(self.index_to_doc_mapping, f)
                
        except Exception as e:
            logging.error(f"Ошибка сохранения векторного хранилища: {e}")
    
    def get_vector_store_size(self) -> int:
        """Получение размера векторного хранилища"""
        return self.vector_store.ntotal if self.vector_store else 0
    
    def get_document_list(self) -> List[str]:
        """Получение списка документов в базе знаний"""
        filenames = set()
        for doc_data in self.document_store.values():
            filenames.add(doc_data.get('filename', 'Unknown'))
        return list(filenames)
    
    def get_last_update_time(self) -> Optional[str]:
        """Получение времени последнего обновления"""
        return self.last_update.isoformat() if self.last_update else None