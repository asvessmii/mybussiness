# Руководство по интеграции ИИ Чат-бота

**Для клиентов и разработчиков**

## Введение

Данное руководство поможет вам быстро интегрировать универсальный ИИ чат-бот в ваш веб-сайт или приложение. Система предоставляет несколько способов интеграции в зависимости от ваших потребностей.

## Способы интеграции

### 1. JavaScript виджет (Рекомендуется)

Самый простой способ добавить чат-бот на ваш сайт.

#### Базовая интеграция

```html
<!-- Добавьте перед закрывающим тегом </body> -->
<div id="ai-chatbot-widget"></div>
<script src="https://your-chatbot-domain.com/widget.js"></script>
<script>
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'light'
});
</script>
```

#### Расширенная настройка

```html
<script>
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'light',                    // 'light' или 'dark'
    position: 'bottom-right',          // 'bottom-right' или 'bottom-left'
    title: 'Помощник по продуктам',
    welcomeMessage: 'Здравствуйте! Я помогу найти информацию о наших продуктах.',
    placeholder: 'Спросите о наших товарах...'
});
</script>
```

### 2. API интеграция

Для более глубокой интеграции используйте REST API.

#### Отправка сообщения

```javascript
async function sendMessage(message, sessionId) {
    const response = await fetch('https://your-chatbot-domain.com/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    });
    
    const data = await response.json();
    return data.response;
}

// Использование
const answer = await sendMessage('Как работает ваш продукт?', 'user-123');
console.log(answer);
```

#### Загрузка документов

```javascript
async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('https://your-chatbot-domain.com/api/upload_document', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}
```

### 3. Встраивание iframe

Простое решение для быстрой интеграции.

```html
<iframe 
    src="https://your-chatbot-domain.com" 
    width="400" 
    height="600"
    frameborder="0">
</iframe>
```

## Настройка для популярных CMS

### WordPress

1. Установите плагин "Insert Headers and Footers"
2. Добавьте код виджета в Footer Scripts
3. Или создайте shortcode для встраивания

```php
// Добавьте в functions.php вашей темы
function chatbot_shortcode($atts) {
    $atts = shortcode_atts(array(
        'title' => 'ИИ Помощник',
        'theme' => 'light'
    ), $atts);
    
    return '<div id="ai-chatbot-widget"></div>
    <script src="https://your-chatbot-domain.com/widget.js"></script>
    <script>
    AIChatbot.init({
        containerId: "ai-chatbot-widget",
        apiUrl: "https://your-chatbot-domain.com/api",
        theme: "' . $atts['theme'] . '",
        title: "' . $atts['title'] . '"
    });
    </script>';
}
add_shortcode('chatbot', 'chatbot_shortcode');
```

Использование: `[chatbot title="Мой помощник" theme="dark"]`

### Shopify

1. Перейдите в админ панель Shopify
2. Online Store → Themes → Actions → Edit code
3. Откройте theme.liquid
4. Добавьте код перед `</body>`

```liquid
<div id="ai-chatbot-widget"></div>
<script src="https://your-chatbot-domain.com/widget.js"></script>
<script>
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'light',
    title: 'Помощник по товарам'
});
</script>
```

### Wix

1. Добавьте HTML элемент на страницу
2. Вставьте код виджета
3. Настройте позиционирование

### Tilda

1. Добавьте блок T123 (HTML)
2. Вставьте код интеграции
3. Опубликуйте страницу

## Кастомизация дизайна

### Темы

Виджет поддерживает светлую и темную темы:

```javascript
// Светлая тема
AIChatbot.init({
    theme: 'light'
});

// Темная тема
AIChatbot.init({
    theme: 'dark'
});
```

### Кастомные стили

Для более глубокой кастомизации добавьте CSS:

```css
/* Изменение цветовой схемы */
.ai-chatbot-widget {
    --primary-color: #007bff;
    --background-color: #ffffff;
    --text-color: #333333;
}

/* Изменение размера виджета */
.ai-chatbot-window {
    width: 450px !important;
    height: 600px !important;
}

/* Скрытие виджета на мобильных устройствах */
@media (max-width: 768px) {
    .ai-chatbot-widget {
        display: none;
    }
}
```

## Управление контентом

### Загрузка документов

Для наполнения базы знаний загрузите документы через API или веб-интерфейс:

```javascript
// Программная загрузка
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);

fetch('https://your-chatbot-domain.com/api/upload_document', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log('Документ загружен:', data));
```

### Поддерживаемые форматы

- PDF документы
- Microsoft Word (.docx)
- Текстовые файлы (.txt)

### Рекомендации по контенту

1. **Структурируйте документы** - используйте заголовки и разделы
2. **Избегайте дублирования** - не загружайте одинаковую информацию
3. **Обновляйте регулярно** - поддерживайте актуальность информации
4. **Используйте ключевые слова** - включайте термины, которые будут искать пользователи

## Мониторинг и аналитика

### Отслеживание использования

```javascript
// Подписка на события виджета
AIChatbot.on('message_sent', function(data) {
    // Отправка в Google Analytics
    gtag('event', 'chatbot_message', {
        'event_category': 'engagement',
        'event_label': data.message
    });
});

AIChatbot.on('widget_opened', function() {
    gtag('event', 'chatbot_opened', {
        'event_category': 'engagement'
    });
});
```

### Метрики для отслеживания

- Количество открытий виджета
- Количество отправленных сообщений
- Время сессии
- Популярные вопросы
- Конверсии после использования чата

## Безопасность

### Настройка CORS

Убедитесь, что ваш домен добавлен в список разрешенных:

```python
# На стороне сервера чат-бота
CORS(app, origins=['https://your-website.com'])
```

### Rate Limiting

API автоматически ограничивает количество запросов:
- 100 запросов в час на IP
- 10 сообщений в минуту на сессию

### Валидация данных

Все входящие данные автоматически валидируются и санитизируются.

## Устранение неполадок

### Виджет не отображается

1. Проверьте консоль браузера на ошибки JavaScript
2. Убедитесь, что URL API корректен
3. Проверьте настройки CORS
4. Убедитесь, что контейнер существует в DOM

### Медленные ответы

1. Проверьте размер базы знаний
2. Оптимизируйте документы (удалите дубли)
3. Свяжитесь с администратором для увеличения ресурсов

### Ошибки API

```javascript
// Обработка ошибок
AIChatbot.on('error', function(error) {
    console.error('Ошибка чат-бота:', error);
    // Показать пользователю сообщение об ошибке
});
```

## Примеры интеграции

### E-commerce сайт

```javascript
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'light',
    title: 'Помощник по товарам',
    welcomeMessage: 'Привет! Помогу найти нужный товар и ответить на вопросы о доставке.',
    placeholder: 'Спросите о товарах, доставке, оплате...'
});

// Интеграция с корзиной
AIChatbot.on('message_sent', function(data) {
    if (data.message.includes('добавить в корзину')) {
        // Логика добавления товара
    }
});
```

### Корпоративный сайт

```javascript
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'dark',
    title: 'Корпоративный помощник',
    welcomeMessage: 'Здравствуйте! Я помогу найти информацию о наших услугах и ответить на ваши вопросы.',
    placeholder: 'Вопросы об услугах, ценах, контактах...'
});
```

### Образовательная платформа

```javascript
AIChatbot.init({
    containerId: 'ai-chatbot-widget',
    apiUrl: 'https://your-chatbot-domain.com/api',
    theme: 'light',
    title: 'Учебный помощник',
    welcomeMessage: 'Привет! Я помогу найти информацию по курсам и ответить на учебные вопросы.',
    placeholder: 'Вопросы по курсам, заданиям, расписанию...'
});
```

## Поддержка

### Техническая поддержка

- Email: support@your-domain.com
- Telegram: @chatbot_support
- Документация: https://docs.your-domain.com

### Часто задаваемые вопросы

**Q: Можно ли изменить дизайн виджета?**
A: Да, виджет поддерживает кастомизацию через CSS и параметры конфигурации.

**Q: Сколько документов можно загрузить?**
A: Ограничения зависят от вашего тарифного плана. Обратитесь к администратору.

**Q: Поддерживается ли многоязычность?**
A: В текущей версии поддерживается русский язык. Многоязычность планируется в следующих обновлениях.

**Q: Можно ли интегрировать с CRM?**
A: Да, через API можно передавать данные в вашу CRM систему.

## Заключение

Интеграция ИИ чат-бота поможет улучшить пользовательский опыт на вашем сайте и автоматизировать ответы на часто задаваемые вопросы. При возникновении вопросов обращайтесь в службу поддержки.

---

**Удачной интеграции! 🚀**

