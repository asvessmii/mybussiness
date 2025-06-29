/**
 * Встраиваемый виджет ИИ чат-бота
 * Для интеграции в клиентские сайты
 */

(function() {
    'use strict';
    
    // Предотвращение повторной инициализации
    if (window.AIChatbot) {
        return;
    }
    
    class AIChatbotWidget {
        constructor() {
            this.config = {
                containerId: null,
                apiUrl: '/api',
                theme: 'light',
                position: 'bottom-right',
                title: 'ИИ Помощник',
                welcomeMessage: 'Здравствуйте! Чем могу помочь?',
                placeholder: 'Введите ваш вопрос...',
                customStyles: {}
            };
            
            this.sessionId = this.generateSessionId();
            this.isOpen = false;
            this.isTyping = false;
            this.messageHistory = [];
            this.widget = null;
            this.events = {};
        }
        
        // Инициализация виджета
        init(options = {}) {
            this.config = { ...this.config, ...options };
            
            if (!this.config.containerId) {
                console.error('AIChatbot: containerId is required');
                return;
            }
            
            this.container = document.getElementById(this.config.containerId);
            if (!this.container) {
                console.error(`AIChatbot: Container with id "${this.config.containerId}" not found`);
                return;
            }
            
            this.createWidget();
            this.bindEvents();
            this.applyCustomStyles();
            
            console.log('AIChatbot widget initialized');
            this.emit('widget_loaded');
        }
        
        // Создание виджета
        createWidget() {
            const widgetHTML = `
                <div class="ai-chatbot-widget ${this.config.theme}" data-position="${this.config.position}">
                    <div class="chatbot-trigger" id="chatbotTrigger">
                        <div class="trigger-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                            </svg>
                        </div>
                        <div class="trigger-close" style="display: none;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                            </svg>
                        </div>
                        <div class="notification-badge" id="notificationBadge" style="display: none;">1</div>
                    </div>
                    
                    <div class="chatbot-window" id="chatbotWindow" style="display: none;">
                        <div class="chatbot-header">
                            <div class="header-info">
                                <div class="bot-avatar">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                    </svg>
                                </div>
                                <div class="header-text">
                                    <div class="bot-name">${this.config.title}</div>
                                    <div class="bot-status">В сети</div>
                                </div>
                            </div>
                            <button class="minimize-btn" id="minimizeBtn">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 13H5v-2h14v2z"/>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="chatbot-messages" id="chatbotMessages">
                            <div class="message bot-message welcome-msg">
                                <div class="message-avatar">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                    </svg>
                                </div>
                                <div class="message-content">
                                    <div class="message-text">${this.config.welcomeMessage}</div>
                                    <div class="message-time">${this.getCurrentTime()}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="chatbot-input">
                            <div class="input-container">
                                <input 
                                    type="text" 
                                    id="chatbotInput" 
                                    placeholder="${this.config.placeholder}"
                                    maxlength="500"
                                    autocomplete="off"
                                >
                                <button id="chatbotSend" class="send-btn" disabled>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                    </svg>
                                </button>
                            </div>
                            <div class="typing-indicator" id="typingIndicator" style="display: none;">
                                <div class="typing-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                                <span class="typing-text">Печатает...</span>
                            </div>
                        </div>
                        
                        <div class="chatbot-footer">
                            <div class="powered-by">
                                Powered by AI Assistant
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            this.container.innerHTML = widgetHTML;
            this.widget = this.container.querySelector('.ai-chatbot-widget');
            
            // Применение стилей
            this.injectStyles();
        }
        
        // Внедрение CSS стилей
        injectStyles() {
            if (document.getElementById('ai-chatbot-styles')) {
                return;
            }
            
            const styles = `
                <style id="ai-chatbot-styles">
                .ai-chatbot-widget {
                    position: fixed;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .ai-chatbot-widget[data-position="bottom-right"] {
                    bottom: 20px;
                    right: 20px;
                }
                
                .ai-chatbot-widget[data-position="bottom-left"] {
                    bottom: 20px;
                    left: 20px;
                }
                
                .chatbot-trigger {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: #2563eb;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                    position: relative;
                }
                
                .chatbot-trigger:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
                }
                
                .notification-badge {
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: #ef4444;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 11px;
                    font-weight: bold;
                }
                
                .chatbot-window {
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 350px;
                    height: 500px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transform: scale(0.8) translateY(20px);
                    opacity: 0;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .ai-chatbot-widget[data-position="bottom-left"] .chatbot-window {
                    right: auto;
                    left: 0;
                }
                
                .chatbot-window.open {
                    transform: scale(1) translateY(0);
                    opacity: 1;
                }
                
                .chatbot-header {
                    background: #2563eb;
                    color: white;
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .header-info {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .bot-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .bot-name {
                    font-weight: 600;
                    font-size: 14px;
                }
                
                .bot-status {
                    font-size: 12px;
                    opacity: 0.8;
                }
                
                .minimize-btn {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: background 0.2s;
                }
                
                .minimize-btn:hover {
                    background: rgba(255,255,255,0.1);
                }
                
                .chatbot-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                
                .message {
                    display: flex;
                    gap: 8px;
                    animation: fadeIn 0.3s ease;
                }
                
                .message.user-message {
                    flex-direction: row-reverse;
                }
                
                .message-avatar {
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                
                .bot-message .message-avatar {
                    background: #e5e7eb;
                    color: #6b7280;
                }
                
                .user-message .message-avatar {
                    background: #2563eb;
                    color: white;
                }
                
                .message-content {
                    max-width: 240px;
                    flex: 1;
                }
                
                .message-text {
                    background: #f3f4f6;
                    padding: 8px 12px;
                    border-radius: 12px;
                    word-wrap: break-word;
                }
                
                .user-message .message-text {
                    background: #2563eb;
                    color: white;
                }
                
                .message-time {
                    font-size: 11px;
                    color: #9ca3af;
                    margin-top: 4px;
                    text-align: center;
                }
                
                .chatbot-input {
                    border-top: 1px solid #e5e7eb;
                    padding: 12px 16px;
                }
                
                .input-container {
                    display: flex;
                    gap: 8px;
                    align-items: flex-end;
                }
                
                .chatbot-input input {
                    flex: 1;
                    border: 1px solid #d1d5db;
                    border-radius: 20px;
                    padding: 8px 16px;
                    outline: none;
                    font-size: 14px;
                    transition: border-color 0.2s;
                }
                
                .chatbot-input input:focus {
                    border-color: #2563eb;
                }
                
                .send-btn {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: #2563eb;
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                
                .send-btn:hover:not(:disabled) {
                    background: #1d4ed8;
                }
                
                .send-btn:disabled {
                    background: #d1d5db;
                    cursor: not-allowed;
                }
                
                .typing-indicator {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-top: 8px;
                    color: #6b7280;
                    font-size: 12px;
                }
                
                .typing-dots {
                    display: flex;
                    gap: 2px;
                }
                
                .typing-dots span {
                    width: 4px;
                    height: 4px;
                    border-radius: 50%;
                    background: #6b7280;
                    animation: typingDots 1.4s infinite ease-in-out;
                }
                
                .typing-dots span:nth-child(2) {
                    animation-delay: 0.2s;
                }
                
                .typing-dots span:nth-child(3) {
                    animation-delay: 0.4s;
                }
                
                .chatbot-footer {
                    padding: 8px 16px;
                    text-align: center;
                    font-size: 11px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                }
                
                /* Темная тема */
                .ai-chatbot-widget.dark .chatbot-window {
                    background: #1f2937;
                    color: #f9fafb;
                }
                
                .ai-chatbot-widget.dark .chatbot-input {
                    border-top-color: #374151;
                }
                
                .ai-chatbot-widget.dark .chatbot-input input {
                    background: #374151;
                    border-color: #4b5563;
                    color: #f9fafb;
                }
                
                .ai-chatbot-widget.dark .message-text {
                    background: #374151;
                    color: #f9fafb;
                }
                
                .ai-chatbot-widget.dark .user-message .message-text {
                    background: #2563eb;
                }
                
                .ai-chatbot-widget.dark .bot-message .message-avatar {
                    background: #4b5563;
                    color: #9ca3af;
                }
                
                .ai-chatbot-widget.dark .chatbot-footer {
                    border-top-color: #374151;
                    color: #6b7280;
                }
                
                /* Анимации */
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes typingDots {
                    0%, 60%, 100% { transform: scale(1); opacity: 0.3; }
                    30% { transform: scale(1.2); opacity: 1; }
                }
                
                /* Мобильная адаптация */
                @media (max-width: 480px) {
                    .chatbot-window {
                        width: 300px;
                        height: 400px;
                        bottom: 70px;
                    }
                    
                    .ai-chatbot-widget[data-position="bottom-left"] .chatbot-window,
                    .ai-chatbot-widget[data-position="bottom-right"] .chatbot-window {
                        right: 10px;
                        left: auto;
                    }
                }
                </style>
            `;
            
            document.head.insertAdjacentHTML('beforeend', styles);
        }
        
        // Привязка событий
        bindEvents() {
            const trigger = this.widget.querySelector('#chatbotTrigger');
            const minimizeBtn = this.widget.querySelector('#minimizeBtn');
            const input = this.widget.querySelector('#chatbotInput');
            const sendBtn = this.widget.querySelector('#chatbotSend');
            
            trigger.addEventListener('click', () => this.toggleWidget());
            minimizeBtn.addEventListener('click', () => this.closeWidget());
            
            input.addEventListener('input', () => this.handleInputChange());
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
            
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // Применение пользовательских стилей
        applyCustomStyles() {
            if (Object.keys(this.config.customStyles).length === 0) return;
            
            const styles = this.config.customStyles;
            const widget = this.widget;
            
            if (styles.primaryColor) {
                const elements = widget.querySelectorAll('.chatbot-trigger, .chatbot-header, .send-btn, .user-message .message-text');
                elements.forEach(el => {
                    el.style.backgroundColor = styles.primaryColor;
                });
            }
            
            if (styles.backgroundColor) {
                const window = widget.querySelector('.chatbot-window');
                if (window) window.style.backgroundColor = styles.backgroundColor;
            }
            
            if (styles.textColor) {
                const window = widget.querySelector('.chatbot-window');
                if (window) window.style.color = styles.textColor;
            }
        }
        
        // Переключение виджета
        toggleWidget() {
            if (this.isOpen) {
                this.closeWidget();
            } else {
                this.openWidget();
            }
        }
        
        // Открытие виджета
        openWidget() {
            const window = this.widget.querySelector('#chatbotWindow');
            const triggerIcon = this.widget.querySelector('.trigger-icon');
            const triggerClose = this.widget.querySelector('.trigger-close');
            
            window.style.display = 'flex';
            setTimeout(() => {
                window.classList.add('open');
            }, 10);
            
            triggerIcon.style.display = 'none';
            triggerClose.style.display = 'flex';
            
            this.isOpen = true;
            this.hideNotificationBadge();
            this.emit('widget_opened');
        }
        
        // Закрытие виджета
        closeWidget() {
            const window = this.widget.querySelector('#chatbotWindow');
            const triggerIcon = this.widget.querySelector('.trigger-icon');
            const triggerClose = this.widget.querySelector('.trigger-close');
            
            window.classList.remove('open');
            setTimeout(() => {
                window.style.display = 'none';
            }, 300);
            
            triggerIcon.style.display = 'flex';
            triggerClose.style.display = 'none';
            
            this.isOpen = false;
            this.emit('widget_closed');
        }
        
        // Обработка изменения ввода
        handleInputChange() {
            const input = this.widget.querySelector('#chatbotInput');
            const sendBtn = this.widget.querySelector('#chatbotSend');
            
            sendBtn.disabled = input.value.trim().length === 0 || this.isTyping;
        }
        
        // Отправка сообщения
        async sendMessage() {
            const input = this.widget.querySelector('#chatbotInput');
            const message = input.value.trim();
            
            if (!message || this.isTyping) return;
            
            // Добавляем сообщение пользователя
            this.addMessage(message, 'user');
            input.value = '';
            this.handleInputChange();
            
            // Показываем индикатор печати
            this.showTypingIndicator();
            
            try {
                const response = await fetch(`${this.config.apiUrl}/chat`, {
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
                    this.addMessage(data.response, 'bot');
                    this.emit('message_received', { message: data.response });
                } else {
                    throw new Error(data.error || 'Ошибка сервера');
                }
            } catch (error) {
                console.error('Ошибка отправки сообщения:', error);
                this.addMessage('Извините, произошла ошибка. Попробуйте позже.', 'bot');
            } finally {
                this.hideTypingIndicator();
            }
            
            this.emit('message_sent', { message: message });
        }
        
        // Добавление сообщения
        addMessage(text, sender) {
            const messagesContainer = this.widget.querySelector('#chatbotMessages');
            const messageEl = document.createElement('div');
            messageEl.className = `message ${sender}-message`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.innerHTML = sender === 'bot' 
                ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>'
                : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>';
            
            const content = document.createElement('div');
            content.className = 'message-content';
            
            const textEl = document.createElement('div');
            textEl.className = 'message-text';
            textEl.textContent = text;
            
            const timeEl = document.createElement('div');
            timeEl.className = 'message-time';
            timeEl.textContent = this.getCurrentTime();
            
            content.appendChild(textEl);
            content.appendChild(timeEl);
            
            messageEl.appendChild(avatar);
            messageEl.appendChild(content);
            
            // Удаляем приветственное сообщение при первом реальном сообщении
            if (sender === 'user') {
                const welcomeMsg = messagesContainer.querySelector('.welcome-msg');
                if (welcomeMsg) welcomeMsg.remove();
            }
            
            messagesContainer.appendChild(messageEl);
            this.scrollToBottom();
            
            // Показываем уведомление если виджет закрыт
            if (!this.isOpen && sender === 'bot') {
                this.showNotificationBadge();
            }
            
            // Сохраняем в истории
            this.messageHistory.push({ text, sender, timestamp: Date.now() });
        }
        
        // Показать индикатор печати
        showTypingIndicator() {
            const indicator = this.widget.querySelector('#typingIndicator');
            indicator.style.display = 'flex';
            this.isTyping = true;
            this.handleInputChange();
            this.scrollToBottom();
        }
        
        // Скрыть индикатор печати
        hideTypingIndicator() {
            const indicator = this.widget.querySelector('#typingIndicator');
            indicator.style.display = 'none';
            this.isTyping = false;
            this.handleInputChange();
        }
        
        // Показать бейдж уведомления
        showNotificationBadge() {
            const badge = this.widget.querySelector('#notificationBadge');
            badge.style.display = 'flex';
        }
        
        // Скрыть бейдж уведомления
        hideNotificationBadge() {
            const badge = this.widget.querySelector('#notificationBadge');
            badge.style.display = 'none';
        }
        
        // Прокрутка к последнему сообщению
        scrollToBottom() {
            const messages = this.widget.querySelector('#chatbotMessages');
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Текущее время
        getCurrentTime() {
            return new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        // Генерация ID сессии
        generateSessionId() {
            return 'widget_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }
        
        // События
        on(event, callback) {
            if (!this.events[event]) {
                this.events[event] = [];
            }
            this.events[event].push(callback);
        }
        
        emit(event, data = {}) {
            if (this.events[event]) {
                this.events[event].forEach(callback => callback(data));
            }
        }
        
        // Публичные методы
        open() {
            this.openWidget();
        }
        
        close() {
            this.closeWidget();
        }
        
        sendBotMessage(message) {
            this.addMessage(message, 'bot');
        }
        
        clearHistory() {
            const messages = this.widget.querySelector('#chatbotMessages');
            messages.innerHTML = `
                <div class="message bot-message welcome-msg">
                    <div class="message-avatar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                    </div>
                    <div class="message-content">
                        <div class="message-text">${this.config.welcomeMessage}</div>
                        <div class="message-time">${this.getCurrentTime()}</div>
                    </div>
                </div>
            `;
            this.messageHistory = [];
            this.sessionId = this.generateSessionId();
        }
    }
    
    // Глобальный объект
    window.AIChatbot = new AIChatbotWidget();
    
})();