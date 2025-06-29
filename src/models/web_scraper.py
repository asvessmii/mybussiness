"""
Продвинутый веб-скрапер с поддержкой JavaScript и различных типов контента
"""

import os
import asyncio
import aiohttp
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
import tempfile
import mimetypes

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import trafilatura
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np

import config
from models.data_processor import DocumentProcessor


class WebScraper:
    """Продвинутый веб-скрапер для сбора данных с различных типов сайтов"""
    
    def __init__(self):
        self.session = None
        self.playwright = None
        self.browser = None
        self.document_processor = DocumentProcessor()
        self.scraped_urls = set()
        self.collected_data = []
        
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_website(self, url: str, max_depth: int = 3, max_pages: int = 50) -> Dict[str, Any]:
        """Основной метод для скрапинга веб-сайта"""
        try:
            logging.info(f"Начинаем скрапинг: {url}")
            
            result = {
                'url': url,
                'status': 'success',
                'pages_scraped': 0,
                'data_collected': [],
                'errors': [],
                'started_at': datetime.now().isoformat(),
                'completed_at': None
            }
            
            # Очистка предыдущих данных
            self.scraped_urls.clear()
            self.collected_data.clear()
            
            # Начинаем скрапинг с главной страницы
            await self._scrape_page_recursive(url, max_depth, max_pages, result)
            
            result['completed_at'] = datetime.now().isoformat()
            result['pages_scraped'] = len(self.scraped_urls)
            result['data_collected'] = self.collected_data
            
            logging.info(f"Скрапинг завершен: {len(self.scraped_urls)} страниц, {len(self.collected_data)} элементов данных")
            
            return result
            
        except Exception as e:
            logging.error(f"Ошибка скрапинга {url}: {e}")
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'pages_scraped': 0,
                'data_collected': [],
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
    
    async def _scrape_page_recursive(self, url: str, depth: int, max_pages: int, result: Dict[str, Any]):
        """Рекурсивный скрапинг страниц"""
        if depth <= 0 or len(self.scraped_urls) >= max_pages or url in self.scraped_urls:
            return
        
        try:
            self.scraped_urls.add(url)
            
            # Скрапинг текущей страницы
            page_data = await self._scrape_single_page(url)
            
            if page_data['status'] == 'success':
                self.collected_data.extend(page_data['data'])
                
                # Поиск ссылок для дальнейшего скрапинга
                if depth > 1:
                    links = page_data.get('links', [])
                    for link in links[:10]:  # Ограничиваем количество ссылок с каждой страницы
                        if len(self.scraped_urls) < max_pages:
                            await self._scrape_page_recursive(link, depth - 1, max_pages, result)
            else:
                result['errors'].append({
                    'url': url,
                    'error': page_data.get('error', 'Unknown error')
                })
                
        except Exception as e:
            logging.error(f"Ошибка при скрапинге страницы {url}: {e}")
            result['errors'].append({
                'url': url,
                'error': str(e)
            })
    
    async def _scrape_single_page(self, url: str) -> Dict[str, Any]:
        """Скрапинг одной страницы с поддержкой JavaScript"""
        try:
            page_data = {
                'url': url,
                'status': 'success',
                'data': [],
                'links': []
            }
            
            # Создаем новую страницу браузера
            page = await self.browser.new_page()
            
            try:
                # Переходим на страницу
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Ждем загрузки динамического контента
                await page.wait_for_timeout(2000)
                
                # Получаем HTML
                html_content = await page.content()
                
                # Извлекаем текст с помощью trafilatura
                text_content = trafilatura.extract(html_content)
                
                if text_content:
                    page_data['data'].append({
                        'type': 'text',
                        'content': text_content,
                        'source': url,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Парсим HTML с BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Извлекаем ссылки
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if self._is_valid_url(full_url, url):
                        links.append(full_url)
                
                page_data['links'] = list(set(links))
                
                # Извлекаем изображения
                await self._extract_images(page, soup, url, page_data)
                
                # Извлекаем таблицы
                self._extract_tables(soup, url, page_data)
                
                # Проверяем наличие PDF и других документов
                await self._extract_documents(page, soup, url, page_data)
                
            finally:
                await page.close()
            
            return page_data
            
        except Exception as e:
            logging.error(f"Ошибка скрапинга страницы {url}: {e}")
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'data': [],
                'links': []
            }
    
    async def _extract_images(self, page, soup: BeautifulSoup, base_url: str, page_data: Dict[str, Any]):
        """Извлечение и обработка изображений с OCR"""
        try:
            images = soup.find_all('img', src=True)
            
            for img in images[:5]:  # Ограничиваем количество изображений
                img_url = urljoin(base_url, img['src'])
                
                try:
                    # Скачиваем изображение
                    async with self.session.get(img_url) as response:
                        if response.status == 200:
                            img_data = await response.read()
                            
                            # Сохраняем во временный файл
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                                tmp_file.write(img_data)
                                tmp_file_path = tmp_file.name
                            
                            try:
                                # OCR обработка
                                ocr_text = await self._extract_text_from_image(tmp_file_path)
                                
                                if ocr_text and len(ocr_text.strip()) > 10:
                                    page_data['data'].append({
                                        'type': 'image_ocr',
                                        'content': ocr_text,
                                        'source': img_url,
                                        'alt_text': img.get('alt', ''),
                                        'timestamp': datetime.now().isoformat()
                                    })
                                
                            finally:
                                # Удаляем временный файл
                                if os.path.exists(tmp_file_path):
                                    os.unlink(tmp_file_path)
                                    
                except Exception as e:
                    logging.warning(f"Ошибка обработки изображения {img_url}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Ошибка извлечения изображений: {e}")
    
    async def _extract_text_from_image(self, image_path: str) -> str:
        """Извлечение текста из изображения с помощью OCR"""
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            
            if image is None:
                return ""
            
            # Предобработка изображения для лучшего OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Улучшение контрастности
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Убираем шум
            denoised = cv2.medianBlur(enhanced, 3)
            
            # OCR с поддержкой русского и английского
            text = pytesseract.image_to_string(denoised, lang='rus+eng')
            
            return text.strip()
            
        except Exception as e:
            logging.error(f"Ошибка OCR обработки {image_path}: {e}")
            return ""
    
    def _extract_tables(self, soup: BeautifulSoup, base_url: str, page_data: Dict[str, Any]):
        """Извлечение данных из таблиц"""
        try:
            tables = soup.find_all('table')
            
            for i, table in enumerate(tables):
                rows = []
                for tr in table.find_all('tr'):
                    row = []
                    for td in tr.find_all(['td', 'th']):
                        row.append(td.get_text(strip=True))
                    if row:
                        rows.append(row)
                
                if rows:
                    # Преобразуем таблицу в текст
                    table_text = "\n".join(["\t".join(row) for row in rows])
                    
                    page_data['data'].append({
                        'type': 'table',
                        'content': table_text,
                        'source': base_url,
                        'table_index': i,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logging.error(f"Ошибка извлечения таблиц: {e}")
    
    async def _extract_documents(self, page, soup: BeautifulSoup, base_url: str, page_data: Dict[str, Any]):
        """Извлечение и обработка документов (PDF, DOC, etc.)"""
        try:
            # Ищем ссылки на документы
            doc_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.txt']):
                    doc_links.append(urljoin(base_url, href))
            
            for doc_url in doc_links[:3]:  # Ограничиваем количество документов
                try:
                    async with self.session.get(doc_url) as response:
                        if response.status == 200:
                            doc_data = await response.read()
                            
                            # Сохраняем во временный файл
                            file_ext = os.path.splitext(doc_url)[1].lower()
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                                tmp_file.write(doc_data)
                                tmp_file_path = tmp_file.name
                            
                            try:
                                # Обрабатываем документ
                                doc_result = self.document_processor.process_document(tmp_file_path)
                                
                                if doc_result['success']:
                                    page_data['data'].append({
                                        'type': 'document',
                                        'content': doc_result['text'],
                                        'source': doc_url,
                                        'file_type': file_ext,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                            finally:
                                if os.path.exists(tmp_file_path):
                                    os.unlink(tmp_file_path)
                                    
                except Exception as e:
                    logging.warning(f"Ошибка обработки документа {doc_url}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Ошибка извлечения документов: {e}")
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """Проверка валидности URL для скрапинга"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Проверяем, что это HTTP/HTTPS
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Проверяем, что это тот же домен или поддомен
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Исключаем некоторые типы файлов
            excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.ico', '.svg']
            if any(url.lower().endswith(ext) for ext in excluded_extensions):
                return False
            
            # Исключаем определенные пути
            excluded_paths = ['/admin', '/login', '/logout', '/register', '/api/']
            if any(path in url.lower() for path in excluded_paths):
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Получение статистики скрапинга"""
        data_types = {}
        for item in self.collected_data:
            data_type = item.get('type', 'unknown')
            data_types[data_type] = data_types.get(data_type, 0) + 1
        
        return {
            'total_urls_scraped': len(self.scraped_urls),
            'total_data_items': len(self.collected_data),
            'data_types': data_types,
            'scraped_urls': list(self.scraped_urls)
        }


class SimpleScraper:
    """Простой синхронный скрапер для базовых случаев"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Простой скрапинг одной страницы"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Извлекаем текст
            text_content = trafilatura.extract(response.text)
            
            if not text_content:
                # Fallback на BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text(strip=True)
            
            return {
                'status': 'success',
                'url': url,
                'content': text_content,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }