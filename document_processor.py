# document_processor.py
import pytesseract
from pdf2image import convert_from_path
from langdetect import detect, LangDetectException
import re

def clean_raw_text(text):
    """
    Базовая очистка текста после OCR: удаление лишних пробелов, переносов строк.
    """
    text = text.replace('\n', ' ') # Заменяем переносы строки на пробелы
    text = re.sub(r'\s+', ' ', text) # Заменяем множественные пробелы на один
    return text.strip()

def process_pdf_document(file_path, tesseract_cmd=None):
    """
    Распознает текст из PDF файла, автоматически определяя язык.
    """
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    try:
        images = convert_from_path(file_path, dpi=300)
    except Exception as e:
        print(f"Не удалось конвертировать PDF в изображения: {file_path}, ошибка: {e}")
        return None
    
    full_text = ''
    for i, image in enumerate(images):
        try:
            # Сначала распознаем с обоими языками для определения доминирующего
            preliminary_text = pytesseract.image_to_string(image, lang='rus+eng')
            
            # Определяем язык
            try:
                lang = detect(preliminary_text)
                lang_tesseract = 'rus' if lang == 'ru' else 'eng'
            except LangDetectException:
                # Если язык не определился, используем оба
                lang_tesseract = 'rus+eng'

            # Финальное распознавание с определенным языком для лучшего качества
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, lang=lang_tesseract, config=custom_config)
            full_text += text + '\n'

        except Exception as e:
            print(f"Ошибка при OCR страницы {i+1} файла {file_path}: {e}")
            continue
            
    return clean_raw_text(full_text)
