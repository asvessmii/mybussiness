# main.py
import os
import json
from tqdm import tqdm

# Импортируем наши модули и конфиг
import config
import crawler
import content_extractor
import document_processor
import text_cleaner

def main():
    # --- Создание необходимых папок ---
    if not os.path.exists(config.DATA_DIRECTORY):
        os.makedirs(config.DATA_DIRECTORY)
    if not os.path.exists(config.PDF_DIRECTORY):
        os.makedirs(config.PDF_DIRECTORY)

    # --- Этап 1: Сбор ссылок ---
    # Проверяем, есть ли уже файл со ссылками, чтобы не собирать их заново
    if os.path.exists(config.LINKS_FILE):
        print(f"Найден файл {config.LINKS_FILE}, использую ссылки из него.")
        with open(config.LINKS_FILE, 'r', encoding='utf-8') as f:
            # Читаем как {title: url}, а нам нужно {url: title}
            lines = f.readlines()
            links_with_titles = {}
            for line in lines:
                if ' - ' in line:
                    title, url = line.strip().split(' - ', 1)
                    links_with_titles[url] = title
    else:
        links_with_titles = crawler.crawl_site(
            config.START_URL, 
            config.ALLOWED_DOMAINS, 
            config.MAX_DEPTH, 
            config.MAX_LINKS
        )
        # Сохраняем найденные ссылки для будущего использования
        with open(config.LINKS_FILE, 'w', encoding='utf-8') as f:
            for url, title in links_with_titles.items():
                f.write(f"{title} - {url}\n")

    # --- Этап 2 и 3: Извлечение контента и обработка ---
    final_dataset = []
    processed_pdfs = set()

    print("\nНачинаю обработку страниц и документов...")
    for url, title in tqdm(links_with_titles.items(), desc="Обработка контента"):
        
        # Обработка HTML страницы
        page_text, pdf_links = content_extractor.extract_content_from_url(url)
    
        if page_text:
            cleaned_page_text = text_cleaner.fully_clean_text(page_text)
            if cleaned_page_text:
                final_dataset.append({
                    "source_type": "webpage",
                    "source_location": url,
                    "title": title,
                    "content": cleaned_page_text
                })

        # Обработка найденных на странице PDF
        for pdf_url in pdf_links:
            if pdf_url in processed_pdfs:
                continue

            print(f"\nНайден PDF: {pdf_url}. Скачиваю и обрабатываю...")
            pdf_path = content_extractor.download_pdf(pdf_url, config.PDF_DIRECTORY)
        
            if pdf_path:
                # Текст из PDF уже прошел базовую чистку, теперь пропускаем через полный конвейер
                pdf_text = document_processor.process_pdf_document(pdf_path, config.TESSERACT_CMD)
                if pdf_text:
                    cleaned_pdf_text = text_cleaner.fully_clean_text(pdf_text)
                    if cleaned_pdf_text:
                        final_dataset.append({
                            "source_type": "pdf",
                            "source_location": pdf_url,
                            "title": os.path.basename(pdf_path),
                            "content": cleaned_pdf_text
                        })
                processed_pdfs.add(pdf_url)

    # --- Этап 4: Сохранение итогового датасета ---
    print(f"\nОбработка завершена. Всего записей в датасете: {len(final_dataset)}")
    with open(config.FINAL_DATASET_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=4)
        
    print(f"Итоговый датасет сохранен в файл: {config.FINAL_DATASET_FILE}")


if __name__ == "__main__":
    main()
