# config.py

# --- Основные настройки ---
# URL сайта, с которого начинаем парсинг
START_URL = "https://www.darwinmuseum.ru" 
# Домен и его поддомены, которые считаются частью "экосистемы"
ALLOWED_DOMAINS = ["darwinmuseum.ru"] 

# --- Настройки краулера ---
MAX_DEPTH = 2  # Максимальная глубина рекурсивного обхода ссылок
MAX_LINKS = 500 # Максимальное количество уникальных ссылок для обработки

# --- Пути к файлам и папкам ---
DATA_DIRECTORY = "data"
PDF_DIRECTORY = f"{DATA_DIRECTORY}/source_pdfs"
LINKS_FILE = "filtered_links.txt"
FINAL_DATASET_FILE = f"{DATA_DIRECTORY}/final_dataset.json"

# --- Настройки Tesseract ---
# Укажите путь к Tesseract OCR, если он не в системном PATH
# Например: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
