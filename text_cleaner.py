import re
import nltk
import pymorphy3
from langdetect import detect, LangDetectException
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# --- Инициализация инструментов (делаем это один раз для производительности) ---
morph = pymorphy3.MorphAnalyzer()
lemmatizer_en = WordNetLemmatizer()

# Загружаем стоп-слова для русского и английского языков
try:
    stopwords_ru = set(stopwords.words('russian'))
    stopwords_en = set(stopwords.words('english'))
except LookupError:
    print("Не найдены пакеты NLTK. Запустите: nltk.download('stopwords')")
    stopwords_ru = set()
    stopwords_en = set()

def remove_artifacts(text):
    """
    Удаляет URL, email, остатки HTML/XML тегов и прочий мусор.
    """
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Удаление URL
    text = re.sub(r'<.*?>', '', text)  # Удаление HTML/XML тегов
    text = re.sub(r'\S+@\S+', '', text)  # Удаление email
    text = re.sub(r'&\w+;', '', text) # Удаление HTML-сущностей типа &nbsp;
    return text

def normalize_text(text):
    """
    Приведение к нижнему регистру, нормализация пробелов и пунктуации.
    """
    text = text.lower()  # Приведение к нижнему регистру
    # Оставляем только буквы, цифры и основные знаки препинания.
    # Это более мягкая чистка, чем в предыдущей версии.
    text = re.sub(r'[^а-яa-z0-9\s.,!?-]', '', text)
    text = re.sub(r'([!?,.-])\1+', r'\1', text)  # Замена !! на ! и т.д.
    text = re.sub(r'\s+', ' ', text).strip()  # Нормализация пробелов
    return text

def lemmatize_and_clean(text, lang, remove_stopwords=False):
    """
    Выполняет токенизацию, лемматизацию и (опционально) удаление стоп-слов.
    """
    # Токенизация (разбиение текста на слова)
    try:
        tokens = word_tokenize(text)
    except LookupError:
        print("Не найден токенизатор NLTK. Запустите: nltk.download('punkt')")
        return text

    lemmatized_tokens = []
    
    # Выбираем стоп-слова в зависимости от языка
    stop_words = set()
    if remove_stopwords:
        if lang == 'ru':
            stop_words = stopwords_ru
        elif lang == 'en':
            stop_words = stopwords_en

    for token in tokens:
        # Пропускаем знаки препинания и короткие слова
        if not token.isalpha() or len(token) < 2:
            continue
        
        # Удаляем стоп-слова, если опция включена
        if remove_stopwords and token in stop_words:
            continue

        # Лемматизация
        if lang == 'ru':
            lemma = morph.parse(token)[0].normal_form
        elif lang == 'en':
            lemma = lemmatizer_en.lemmatize(token)
        else:
            lemma = token # Если язык не определен, оставляем как есть
        
        lemmatized_tokens.append(lemma)

    return ' '.join(lemmatized_tokens)


def fully_clean_text(text, remove_stopwords=False):
    """
    Полный конвейер очистки текста: артефакты -> нормализация -> лемматизация.
    Рекомендуется remove_stopwords=False для современных QA моделей.
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Удаление технических артефактов
    text = remove_artifacts(text)
    
    # 2. Базовая нормализация текста
    text = normalize_text(text)

    # 3. Определение языка для дальнейшей обработки
    try:
        lang = detect(text)
    except LangDetectException:
        lang = 'unknown' # Если не удалось определить, пропускаем лемматизацию

    # 4. Лемматизация и финальная очистка
    if lang in ['ru', 'en']:
        text = lemmatize_and_clean(text, lang, remove_stopwords=remove_stopwords)
    
    return text
