/**
 * Универсальный ИИ Чат-бот - Клиентская логика
 */

class ChatbotUI {
    constructor() {
        this.apiUrl = '/api'; // API префикс для корректной работы
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.isTyping = false;
        this.settings = {
            apiUrl: '/api',
            maxDocs: 5
        };
        
        this.initializeElements();
        this.bindEvents();
        this.checkSystemStatus();
        this.loadSettings();
        
        console.log('Chatbot UI initialized with session:', this.sessionId);
    }
    
    // Инициализация элементов DOM
    initializeElements() {
        this.elements = {
            // Статус
            statusIndicator: document.getElementById('statusIndicator'),
            statusDot: document.querySelector('.status-dot'),
            statusText: document.querySelector('.status-text'),
            
            // Загрузка файлов
            uploadArea: document.getElementById('uploadArea'),
            fileInput: document.getElementById('fileInput'),
            uploadProgress: document.getElementById('uploadProgress'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            
            // База знаний
            kbStats: document.getElementById('kbStats'),
            docCount: document.getElementById('docCount'),
            vectorCount: document.getElementById('vectorCount'),
            refreshStats: document.getElementById('refreshStats'),
            
            // Чат
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            clearChatBtn: document.getElementById('clearChatBtn'),
            charCounter: document.getElementById('charCounter'),
            typingIndicator: document.getElementById('typingIndicator'),
            
            // Настройки
            settingsBtn: document.getElementById('settingsBtn'),
            settingsModal: document.getElementById('settingsModal'),
            closeModal: document.getElementById('closeModal'),
            apiUrlInput: document.getElementById('apiUrl'),
            maxDocsInput: document.getElementById('maxDocs'),
            saveSettings: document.getElementById('saveSettings'),
            cancelSettings: document.getElementById('cancelSettings'),
            
            // Уведомления
            notifications: document.getElementById('notifications')
        };
        
        // Отладочная информация
        console.log('DOM элементы инициализированы:');
        console.log('statusIndicator:', this.elements.statusIndicator);
        console.log('statusDot:', this.elements.statusDot);
        console.log('statusText:', this.elements.statusText);
        console.log('messageInput:', this.elements.messageInput);
        console.log('sendButton:', this.elements.sendButton);
    }
    
    // Привязка событий
    bindEvents() {
        // Загрузка файлов
        this.elements.uploadArea.addEventListener('click', () => {
            this.elements.fileInput.click();
        });
        
        this.elements.fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
        
        // Drag & Drop
        this.elements.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.add('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('dragleave', () => {
            this.elements.uploadArea.classList.remove('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.remove('drag-over');
            this.handleFileUpload(e.dataTransfer.files);
        });
        
        // Чат
        this.elements.messageInput.addEventListener('input', (e) => {
            this.updateCharCounter();
            this.toggleSendButton();
        });
        
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.elements.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        this.elements.clearChatBtn.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Статистика
        this.elements.refreshStats.addEventListener('click', () => {
            this.updateKnowledgeBaseStats();
        });
        
        // Настройки
        this.elements.settingsBtn.addEventListener('click', () => {
            this.openSettings();
        });
        
        this.elements.closeModal.addEventListener('click', () => {
            this.closeSettings();
        });
        
        this.elements.cancelSettings.addEventListener('click', () => {
            this.closeSettings();
        });
        
        this.elements.saveSettings.addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Закрытие модального окна по клику вне его
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) {
                this.closeSettings();
            }
        });
    }
    
    // Генерация уникального ID сессии
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    // Проверка статуса системы
    async checkSystemStatus() {
        console.log('Проверка статуса системы...');
        console.log('API URL:', this.apiUrl);
        
        try {
            const response = await fetch(`${this.apiUrl}/status`);
            console.log('Ответ сервера:', response.status, response.statusText);
            
            const data = await response.json();
            console.log('Данные ответа:', data);
            
            if (response.ok) {
                this.updateStatus('online', 'Система готова');
                this.isConnected = true;
                this.updateKnowledgeBaseStats(data);
                console.log('Соединение установлено');
            } else {
                throw new Error(data.message || 'Ошибка сервера');
            }
        } catch (error) {
            console.error('Ошибка проверки статуса:', error);
            this.updateStatus('offline', 'Нет соединения');
            this.isConnected = false;
        }
    }
    
    // Обновление индикатора статуса
    updateStatus(status, text) {
        this.elements.statusDot.className = `status-dot ${status}`;
        this.elements.statusText.textContent = text;
    }
    
    // Обработка загрузки файлов
    async handleFileUpload(files) {
        if (!files || files.length === 0) return;
        
        const file = files[0];
        const maxSize = 16 * 1024 * 1024; // 16MB
        
        // Проверка размера файла
        if (file.size > maxSize) {
            this.showNotification('Файл слишком большой. Максимальный размер: 16MB', 'error');
            return;
        }
        
        // Проверка формата файла
        const allowedTypes = ['.pdf', '.docx', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showNotification('Неподдерживаемый формат файла. Разрешены: PDF, DOCX, TXT', 'error');
            return;
        }
        
        try {
            this.showUploadProgress(true);
            this.updateUploadProgress(0);
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${this.apiUrl}/upload_document`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateUploadProgress(100);
                this.showNotification(`Документ "${file.name}" успешно загружен`, 'success');
                this.updateKnowledgeBaseStats();
                
                setTimeout(() => {
                    this.showUploadProgress(false);
                }, 1000);
            } else {
                throw new Error(data.error || 'Ошибка загрузки');
            }
        } catch (error) {
            console.error('Ошибка загрузки файла:', error);
            this.showNotification(`Ошибка загрузки: ${error.message}`, 'error');
            this.showUploadProgress(false);
        }
    }
    
    // Показать/скрыть прогресс загрузки
    showUploadProgress(show) {
        this.elements.uploadProgress.style.display = show ? 'block' : 'none';
        this.elements.uploadArea.classList.toggle('processing', show);
    }
    
    // Обновить прогресс загрузки
    updateUploadProgress(percent) {
        this.elements.progressFill.style.width = `${percent}%`;
        this.elements.progressText.textContent = `${percent}%`;
    }
    
    // Обновление статистики базы знаний
    async updateKnowledgeBaseStats(data = null) {
        try {
            if (!data) {
                const response = await fetch(`${this.apiUrl}/knowledge_base`);
                data = await response.json();
            }
            
            if (data) {
                this.elements.vectorCount.textContent = data.vector_store_size || 0;
                this.elements.docCount.textContent = data.total_documents || 0;
            }
        } catch (error) {
            console.error('Ошибка получения статистики:', error);
        }
    }
    
    // Отправка сообщения
    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        
        if (!message || this.isTyping) return;
        
        if (!this.isConnected) {
            this.showNotification('Нет соединения с сервером', 'error');
            return;
        }
        
        try {
            // Добавляем сообщение пользователя
            this.addMessage(message, 'user');
            this.elements.messageInput.value = '';
            this.updateCharCounter();
            this.toggleSendButton();
            
            // Показываем индикатор печати
            this.showTypingIndicator(true);
            this.isTyping = true;
            
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Добавляем ответ бота
                this.addMessage(data.response, 'bot');
            } else {
                throw new Error(data.error || 'Ошибка сервера');
            }
        } catch (error) {
            console.error('Ошибка отправки сообщения:', error);
            this.addMessage('Извините, произошла ошибка при обработке вашего сообщения.', 'bot');
            this.showNotification(`Ошибка: ${error.message}`, 'error');
        } finally {
            this.showTypingIndicator(false);
            this.isTyping = false;
        }
    }
    
    // Добавление сообщения в чат
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const textElement = document.createElement('p');
        textElement.textContent = text;
        
        const timeElement = document.createElement('small');
        timeElement.className = 'message-time';
        timeElement.textContent = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        content.appendChild(textElement);
        content.appendChild(timeElement);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        // Удаляем приветственное сообщение при первом реальном сообщении
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage && sender === 'user') {
            welcomeMessage.remove();
        }
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    // Прокрутка чата вниз
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    // Показать/скрыть индикатор печати
    showTypingIndicator(show) {
        this.elements.typingIndicator.style.display = show ? 'inline-flex' : 'none';
    }
    
    // Обновление счетчика символов
    updateCharCounter() {
        const length = this.elements.messageInput.value.length;
        this.elements.charCounter.textContent = `${length}/500`;
        
        if (length > 450) {
            this.elements.charCounter.style.color = 'var(--warning-color)';
        } else if (length > 480) {
            this.elements.charCounter.style.color = 'var(--error-color)';
        } else {
            this.elements.charCounter.style.color = 'var(--text-secondary)';
        }
    }
    
    // Переключение кнопки отправки
    toggleSendButton() {
        const hasText = this.elements.messageInput.value.trim().length > 0;
        this.elements.sendButton.disabled = !hasText || !this.isConnected || this.isTyping;
    }
    
    // Очистка чата
    clearChat() {
        if (confirm('Очистить историю чата?')) {
            this.elements.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <div class="message bot-message">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            <p>Здравствуйте! Я ИИ помощник. Загрузите документы и задавайте вопросы по их содержанию.</p>
                            <small class="message-time">Чат очищен</small>
                        </div>
                    </div>
                </div>
            `;
            
            // Генерируем новый session ID
            this.sessionId = this.generateSessionId();
            
            this.showNotification('Чат очищен', 'info');
        }
    }
    
    // Показать уведомление
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        this.elements.notifications.appendChild(notification);
        
        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Удаление по клику
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    // Открыть настройки
    openSettings() {
        this.elements.apiUrlInput.value = this.settings.apiUrl;
        this.elements.maxDocsInput.value = this.settings.maxDocs;
        this.elements.settingsModal.style.display = 'flex';
    }
    
    // Закрыть настройки
    closeSettings() {
        this.elements.settingsModal.style.display = 'none';
    }
    
    // Сохранить настройки
    saveSettings() {
        this.settings.apiUrl = this.elements.apiUrlInput.value || '/api';
        this.settings.maxDocs = parseInt(this.elements.maxDocsInput.value) || 5;
        
        this.apiUrl = this.settings.apiUrl;
        
        // Сохранение в localStorage
        localStorage.setItem('chatbot_settings', JSON.stringify(this.settings));
        
        this.closeSettings();
        this.showNotification('Настройки сохранены', 'success');
        
        // Перепроверка статуса с новыми настройками
        this.checkSystemStatus();
    }
    
    // Загрузка настроек
    loadSettings() {
        try {
            const saved = localStorage.getItem('chatbot_settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
                this.apiUrl = this.settings.apiUrl;
            }
        } catch (error) {
            console.warn('Ошибка загрузки настроек:', error);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new ChatbotUI();
    
    // Периодическая проверка статуса каждые 30 секунд
    setInterval(() => {
        window.chatbot.checkSystemStatus();
    }, 30000);
});

// Глобальная обработка ошибок
window.addEventListener('error', (event) => {
    console.error('Глобальная ошибка:', event.error);
    if (window.chatbot) {
        window.chatbot.showNotification('Произошла непредвиденная ошибка', 'error');
    }
});

// Обработка потери соединения
window.addEventListener('offline', () => {
    if (window.chatbot) {
        window.chatbot.updateStatus('offline', 'Нет соединения');
        window.chatbot.isConnected = false;
        window.chatbot.toggleSendButton();
        window.chatbot.showNotification('Соединение потеряно', 'warning');
    }
});

window.addEventListener('online', () => {
    if (window.chatbot) {
        window.chatbot.checkSystemStatus();
        window.chatbot.showNotification('Соединение восстановлено', 'success');
    }
});