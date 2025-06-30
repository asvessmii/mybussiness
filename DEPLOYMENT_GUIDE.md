# 🚀 Инструкция по развертыванию ИИ Чат-бота

## 📋 Обзор системы

Данная система представляет собой **Универсальный ИИ Чат-бот** - интеллектуальную QA систему для создания специализированных чат-ботов, обученных на данных конкретных веб-сайтов и доменных областей.

## 💻 Техническая архитектура

- **Backend**: Flask + Python 3.11
- **ИИ/ML**: Sentence Transformers, FAISS, PyTorch
- **База данных**: MongoDB + SQLite
- **Фронтенд**: HTML/CSS/JavaScript
- **Веб-скрапинг**: Playwright, BeautifulSoup, Trafilatura

## 🔧 Системные требования

### Минимальные:
- Python 3.8+
- 8 GB RAM
- 10 GB свободного места
- Интернет-соединение

### Рекомендуемые:
- Python 3.11+
- 16+ GB RAM
- SSD накопитель
- GPU (опционально)

## 🚀 Пошаговое развертывание

### Шаг 1: Подготовка окружения

```bash
# Клонирование репозитория (если используется Git)
git clone <your-repository>
cd <project-directory>

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### Шаг 2: Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Для Ubuntu/Debian дополнительно установите:
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

### Шаг 3: Настройка конфигурации

```bash
# Проверьте конфигурацию в config.py
# Убедитесь, что пути корректны для вашей системы

# Создайте необходимые директории
mkdir -p uploads vector_store logs
```

### Шаг 4: Настройка Supervisor (Production)

**Внимание**: Для корректной работы необходимо настроить supervisor с правильными путями.

Пример конфигурации `/etc/supervisor/conf.d/chatbot.conf`:

```ini
[program:chatbot]
command=/path/to/your/venv/bin/python simple_server.py
directory=/path/to/your/project
user=your-user
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/chatbot.err.log
stdout_logfile=/var/log/supervisor/chatbot.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/path/to/your/project"
```

### Шаг 5: Запуск системы

#### Вариант A: Запуск через Supervisor (Production)
```bash
# Перезагрузка конфигурации supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Запуск сервиса
sudo supervisorctl start chatbot

# Проверка статуса
sudo supervisorctl status
```

#### Вариант B: Ручной запуск (Development)
```bash
# Простая демо-версия
python simple_server.py

# Или полная версия с ИИ моделями
python src/main.py
```

### Шаг 6: Проверка работоспособности

```bash
# Проверка API
curl http://localhost:3000/api/status

# Проверка веб-интерфейса
curl http://localhost:3000/

# Проверка чата
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Привет","session_id":"test"}'
```

## 🌐 Доступ к системе

После успешного запуска система будет доступна:

- **Главная страница**: http://localhost:3000/
- **API статус**: http://localhost:3000/api/status
- **Админ-панель**: http://localhost:3000/static/admin.html
- **Виджет**: http://localhost:3000/widget.js

## 🔑 Ключевые особенности развертывания

### 1. Порты и URL-адреса
- **По умолчанию**: Приложение работает на порту 3000
- **Не изменяйте** порт без соответствующих изменений в коде
- Все API endpoints должны иметь префикс `/api/`

### 2. Статические файлы
Статические файлы находятся в `/src/static/`:
- `index.html` - главная страница
- `admin.html` - админ-панель  
- `script.js` - логика главной страницы
- `admin.js` - логика админ-панели
- `styles.css`, `admin.css` - стили

### 3. Логи и мониторинг
```bash
# Просмотр логов supervisor
tail -f /var/log/supervisor/chatbot.out.log
tail -f /var/log/supervisor/chatbot.err.log

# Проверка статуса процессов
sudo supervisorctl status

# Перезапуск при необходимости
sudo supervisorctl restart chatbot
```

## 🛠 Устранение неполадок

### Проблема: "No module named 'backend'"
**Решение**: Убедитесь, что supervisor настроен для запуска `simple_server.py`, а не FastAPI приложения.

### Проблема: "Нет соединения с сервером" в чате
**Решение**: 
1. Проверьте, что в `script.js` установлен `apiUrl = '/api'`
2. Убедитесь, что сервер запущен на порту 3000
3. Проверьте доступность API: `curl http://localhost:3000/api/status`

### Проблема: Кнопки в админ-панели не работают
**Решение**: Убедитесь, что файл `admin.js` существует и корректно загружается.

### Проблема: Ошибки при установке зависимостей
**Решение**:
```bash
# Обновите pip
pip install --upgrade pip

# Установите системные зависимости
sudo apt-get install python3-dev build-essential

# Переустановите проблемные пакеты
pip install --force-reinstall <package-name>
```

## 🔧 Настройка для production

### 1. Настройка веб-сервера (nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. SSL сертификат
```bash
# Используйте Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 3. Переменные окружения
Создайте `.env` файл для production настроек:
```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=your-database-url
```

## 📊 Мониторинг в production

### 1. Здоровье системы
Регулярно проверяйте `/api/status` endpoint

### 2. Логирование
```bash
# Настройте ротацию логов
sudo logrotate /etc/logrotate.d/chatbot
```

### 3. Ресурсы системы
```bash
# Мониторинг использования памяти и CPU
htop
free -h
df -h
```

## 🔄 Обновление системы

### 1. Резервное копирование
```bash
# Сохраните базы данных и загруженные файлы
cp -r uploads uploads_backup
cp projects.db projects_backup.db
```

### 2. Обновление кода
```bash
# Остановите сервис
sudo supervisorctl stop chatbot

# Обновите код
git pull origin main

# Установите новые зависимости
pip install -r requirements.txt

# Запустите сервис
sudo supervisorctl start chatbot
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `/var/log/supervisor/chatbot.*.log`
2. Убедитесь в правильности конфигурации supervisor
3. Проверьте доступность всех зависимостей
4. Убедитесь в корректности путей в `config.py`

## 🎯 Что дальше?

После успешного развертывания вы можете:
1. **Создать первый проект** через админ-панель
2. **Загрузить документы** для обучения
3. **Настроить веб-скрапинг** для автоматического сбора данных
4. **Интегрировать виджет** в ваш сайт
5. **Настроить автоматические обновления** базы знаний

---

**Дата создания**: $(date)  
**Версия системы**: 1.0.0  
**Протестировано на**: Python 3.11, Ubuntu 20.04/22.04