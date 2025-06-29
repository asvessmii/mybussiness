# crawler.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
from tqdm import tqdm

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

def is_valid_url(url, allowed_domains):
    """
    Проверяет, что URL относится к разрешенным доменам и не ведет на медиа-файлы или документы.
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https'
                                 ]:
        return False
    
    # Проверка, что домен принадлежит экосистеме
    if not any(parsed_url.netloc.endswith(domain) for domain in allowed_domains):
        return False
        
    # Отсеиваем ссылки на файлы (кроме .pdf, которые мы обработаем отдельно)
    blacklisted_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.css', '.js', '.xml', '.mp3', '.mp4']
    if any(parsed_url.path.lower().endswith(ext) for ext in blacklisted_extensions):
        return False

    return True

def crawl_site(start_url, allowed_domains, max_depth, max_links):
    """
    Собирает все валидные внутренние ссылки сайта.
    """
    print("Начинаю сбор ссылок...")
    links_to_process = [(start_url, 0)]
    visited_links = set()
    collected_links = {} # Словарь для хранения {url: title}

    pbar = tqdm(total=max_links, desc="Сбор ссылок")

    while links_to_process and len(visited_links) < max_links:
        current_url, depth = links_to_process.pop(0)
        
        # Нормализуем URL
        current_url, _ = urldefrag(current_url)

        if current_url in visited_links:
            continue
        
        if depth > max_depth:
            continue

        try:
            response = requests.get(current_url, headers=headers, timeout=10, allow_redirects=True)
            visited_links.add(current_url)
            pbar.update(1)

            if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.content, 'lxml')
                
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else 'Без названия'
                
                # Сохраняем только валидные ссылки
                if is_valid_url(current_url, allowed_domains):
                    collected_links[current_url] = title_text

                # Ищем новые ссылки для обхода
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(current_url, link['href'])
                    full_url, _ = urldefrag(full_url)
                    
                    if full_url not in visited_links and is_valid_url(full_url, allowed_domains):
                        links_to_process.append((full_url, depth + 1))
            
            time.sleep(0.1) # Небольшая задержка

        except requests.RequestException as e:
            print(f"Ошибка при обработке {current_url}: {e}")
            visited_links.add(current_url) # Добавляем в посещенные, чтобы не пробовать снова
            pbar.update(1)


    pbar.close()
    print(f"Сбор ссылок завершен. Найдено {len(collected_links)} уникальных страниц.")
    return collected_links
