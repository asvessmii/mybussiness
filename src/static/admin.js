/**
 * Админ-панель - Управление проектами ИИ чат-ботов
 */

class AdminPanel {
    constructor() {
        this.apiUrl = '/api';
        this.currentProject = null;
        this.projects = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadProjects();
        
        console.log('Админ-панель инициализирована');
    }
    
    initializeElements() {
        this.elements = {
            // Навигация
            navItems: document.querySelectorAll('.nav-item'),
            contentSections: document.querySelectorAll('.content-section'),
            
            // Проекты
            projectsGrid: document.getElementById('projects-grid'),
            projectsLoading: document.getElementById('projects-loading'),
            
            // Форма создания проекта
            projectForm: document.getElementById('project-form'),
            projectName: document.getElementById('project-name'),
            projectUrl: document.getElementById('project-url'),
            
            // Детали проекта
            projectDetailTitle: document.getElementById('project-detail-title'),
            projectDetailContent: document.getElementById('project-detail-content'),
            
            // Чат
            chatTitle: document.getElementById('chat-title'),
            chatMessages: document.getElementById('chat-messages'),
            chatInput: document.getElementById('chat-input'),
            
            // Модальные окна
            modalOverlay: document.getElementById('modal-overlay'),
            codeModal: document.getElementById('code-modal'),
            codeDisplay: document.getElementById('code-display'),
            
            // Уведомления
            notifications: document.getElementById('notifications')
        };
    }
    
    bindEvents() {
        // Навигация
        this.elements.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.showSection(section);
                this.setActiveNavItem(item);
            });
        });
        
        // Форма создания проекта
        if (this.elements.projectForm) {
            this.elements.projectForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createProject();
            });
        }
        
        // Чат
        if (this.elements.chatInput) {
            this.elements.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }
    }
    
    // Показать секцию
    showSection(sectionName) {
        this.elements.contentSections.forEach(section => {
            section.classList.remove('active');
        });
        
        const targetSection = document.getElementById(sectionName + '-section');
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Особые действия для разных секций
        if (sectionName === 'projects') {
            this.loadProjects();
        }
    }
    
    // Установить активный пункт навигации
    setActiveNavItem(activeItem) {
        this.elements.navItems.forEach(item => {
            item.classList.remove('active');
        });
        activeItem.classList.add('active');
    }
    
    // Загрузка проектов
    async loadProjects() {
        this.showLoading(true);
        
        try {
            const response = await fetch(this.apiUrl + '/projects');
            const data = await response.json();
            
            if (response.ok) {
                this.projects = data.projects || [];
                this.renderProjects();
            } else {
                throw new Error(data.error || 'Ошибка загрузки проектов');
            }
        } catch (error) {
            console.error('Ошибка загрузки проектов:', error);
            this.showNotification('Ошибка загрузки проектов: ' + error.message, 'error');
            this.projects = [];
            this.renderProjects();
        } finally {
            this.showLoading(false);
        }
    }
    
    // Отображение проектов
    renderProjects() {
        if (!this.elements.projectsGrid) return;
        
        if (this.projects.length === 0) {
            this.elements.projectsGrid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #6c757d;"><i class="fas fa-project-diagram" style="font-size: 3rem; margin-bottom: 20px; opacity: 0.5;"></i><h3>Пока нет проектов</h3><p>Создайте первый проект, чтобы начать работу с ИИ чат-ботами</p><button class="btn btn-primary" onclick="showCreateProject()" style="margin-top: 20px;"><i class="fas fa-plus"></i> Создать проект</button></div>';
            return;
        }
        
        this.elements.projectsGrid.innerHTML = this.projects.map(project => 
            '<div class="project-card">' +
                '<div class="project-header">' +
                    '<h3 class="project-title">' + this.escapeHtml(project.name) + '</h3>' +
                    '<span class="project-status status-' + project.status + '">' + this.getStatusText(project.status) + '</span>' +
                '</div>' +
                '<div class="project-url">' + this.escapeHtml(project.url) + '</div>' +
                '<div class="project-meta">' +
                    '<span>Создан: ' + this.formatDate(project.created_at) + '</span>' +
                    '<span>ID: ' + project.id + '</span>' +
                '</div>' +
                '<div class="project-actions">' +
                    '<button class="btn btn-info" onclick="showProjectDetail(\'' + project.id + '\')">' +
                        '<i class="fas fa-eye"></i> Детали' +
                    '</button>' +
                    (project.status === 'ready' ? 
                        '<button class="btn btn-success" onclick="testProjectChat(\'' + project.id + '\', \'' + this.escapeHtml(project.name) + '\')">' +
                            '<i class="fas fa-comments"></i> Тест' +
                        '</button>' +
                        '<button class="btn btn-primary" onclick="generateCode(\'' + project.id + '\')">' +
                            '<i class="fas fa-code"></i> Код' +
                        '</button>' : '') +
                    (project.status === 'created' ? 
                        '<button class="btn btn-warning" onclick="startScraping(\'' + project.id + '\')">' +
                            '<i class="fas fa-spider"></i> Запустить' +
                        '</button>' : '') +
                    '<button class="btn btn-danger" onclick="deleteProject(\'' + project.id + '\')">' +
                        '<i class="fas fa-trash"></i> Удалить' +
                    '</button>' +
                '</div>' +
            '</div>'
        ).join('');
    }
    
    // Создание проекта
    async createProject() {
        const name = this.elements.projectName.value.trim();
        const url = this.elements.projectUrl.value.trim();
        
        if (!name || !url) {
            this.showNotification('Заполните все поля', 'error');
            return;
        }
        
        try {
            const response = await fetch(this.apiUrl + '/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: name, url: url })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Проект создан успешно!', 'success');
                this.elements.projectForm.reset();
                this.showSection('projects');
                this.loadProjects();
            } else {
                throw new Error(data.error || 'Ошибка создания проекта');
            }
        } catch (error) {
            console.error('Ошибка создания проекта:', error);
            this.showNotification('Ошибка создания проекта: ' + error.message, 'error');
        }
    }
    
    // Показать/скрыть загрузку
    showLoading(show) {
        if (this.elements.projectsLoading) {
            this.elements.projectsLoading.style.display = show ? 'block' : 'none';
        }
    }
    
    // Показать уведомление
    showNotification(message, type) {
        type = type || 'info';
        const notification = document.createElement('div');
        notification.className = 'notification ' + type;
        notification.innerHTML = '<i class="fas fa-' + this.getNotificationIcon(type) + '"></i><span>' + message + '</span>';
        
        this.elements.notifications.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    // Получить иконку для уведомления
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    // Получить текст статуса
    getStatusText(status) {
        const statusTexts = {
            created: 'Создан',
            scraping: 'Обработка',
            scraped: 'Обработан',
            training: 'Обучение',
            ready: 'Готов',
            error: 'Ошибка'
        };
        return statusTexts[status] || status;
    }
    
    // Форматирование даты
    formatDate(dateString) {
        if (!dateString) return 'Неизвестно';
        return new Date(dateString).toLocaleString('ru-RU');
    }
    
    // Экранирование HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Глобальные функции для вызова из HTML
function showSection(sectionName) {
    if (window.adminPanel) {
        window.adminPanel.showSection(sectionName);
    }
}

function showProjects() {
    showSection('projects');
}

function showCreateProject() {
    showSection('create-project');
}

function showProjectDetail(projectId) {
    if (window.adminPanel) {
        window.adminPanel.showProjectDetail(projectId);
    }
}

function testProjectChat(projectId, projectName) {
    if (window.adminPanel) {
        window.adminPanel.testProjectChat(projectId, projectName);
    }
}

function generateCode(projectId) {
    if (window.adminPanel) {
        window.adminPanel.generateCode(projectId);
    }
}

function startScraping(projectId) {
    if (window.adminPanel) {
        fetch('/api/projects/' + projectId + '/scrape', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.adminPanel.showNotification('Ошибка: ' + data.error, 'error');
                } else {
                    window.adminPanel.showNotification('Обработка запущена!', 'success');
                    setTimeout(() => window.adminPanel.loadProjects(), 2000);
                }
            })
            .catch(error => {
                window.adminPanel.showNotification('Ошибка запуска: ' + error.message, 'error');
            });
    }
}

function deleteProject(projectId) {
    if (confirm('Вы уверены, что хотите удалить этот проект?')) {
        fetch('/api/projects/' + projectId, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.adminPanel.showNotification('Ошибка: ' + data.error, 'error');
                } else {
                    window.adminPanel.showNotification('Проект удален!', 'success');
                    window.adminPanel.loadProjects();
                }
            })
            .catch(error => {
                window.adminPanel.showNotification('Ошибка удаления: ' + error.message, 'error');
            });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
});
