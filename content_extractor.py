# content_extractor.py
import requests
import os
import trafilatura
from urllib.parse import urljoin, urlparse

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

def extract_content_from_url(url):
    """
    Скачивает страницу и извлекает из нее только основной контент.
    """
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None, []
        
    # Извлекаем основной текст
    main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
    
    # Ищем PDF-ссылки на странице с помощью BeautifulSoup, так как trafilatura это не делает
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(downloaded, 'lxml')
    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf'):
            pdf_url = urljoin(url, href)
            pdf_links.append(pdf_url)
            
    return main_text, pdf_links

def download_pdf(pdf_url, save_dir):
    """
    Скачивает PDF файл по ссылке и сохраняет его.
    """
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Создаем корректное имя файла
        pdf_name = os.path.basename(urlparse(pdf_url).path)
        if not pdf_name:
            pdf_name = pdf_url.split('/')[-1]
            if not pdf_name.endswith('.pdf'):
                 pdf_name += '.pdf'

        pdf_path = os.path.join(save_dir, pdf_name)
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        return pdf_path
    except requests.RequestException as e:
        print(f"Ошибка при скачивании PDF {pdf_url}: {e}")
        return None
