// static/js/chat.js
class ChatManager {
    constructor(channelId, userId, username) {
        this.channelId = channelId;
        this.userId = userId;
        this.username = username;
        this.socket = null;
        this.typingTimeout = null;
        this.messageContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendMessageBtn');
        
        this.init();
    }
    
    init() {
        if (!this.channelId) return;
        
        this.connectWebSocket();
        this.setupEventListeners();
        this.scrollToBottom();
        this.loadOlderMessages();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = new WebSocket(
            `${protocol}//${window.location.host}/ws/chat/${this.channelId}/`
        );
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleMessage(data);
        };
        
        this.socket.onclose = (e) => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    setupEventListeners() {
        // Отправка сообщения по кнопке
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Отправка по Enter
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Индикатор печати
        this.messageInput.addEventListener('input', () => {
            this.sendTypingIndicator();
        });
        
        // Контекстное меню для сообщений
        this.messageContainer.addEventListener('contextmenu', (e) => {
            const messageElement = e.target.closest('.message');
            if (messageElement) {
                e.preventDefault();
                this.showContextMenu(e.clientX, e.clientY, messageElement);
            }
        });
        
        // Бесконечная прокрутка вверх для загрузки старых сообщений
        this.messageContainer.addEventListener('scroll', () => {
            if (this.messageContainer.scrollTop === 0) {
                this.loadOlderMessages();
            }
        });
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.socket || this.socket.readyState !== WebSocket.OPEN) return;
        
        this.socket.send(JSON.stringify({
            type: 'message',
            message: message,
            channel_id: this.channelId
        }));
        
        this.messageInput.value = '';
        this.clearTypingIndicator();
    }
    
    sendTypingIndicator() {
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        } else {
            this.socket.send(JSON.stringify({
                type: 'typing',
                channel_id: this.channelId
            }));
        }
        
        this.typingTimeout = setTimeout(() => {
            this.typingTimeout = null;
        }, 2000);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'chat_message':
                this.addMessage(data);
                break;
            case 'user_typing':
                this.showTypingIndicator(data.username);
                break;
            case 'user_join':
                this.showSystemMessage(`${data.username} присоединился к каналу`);
                break;
            case 'user_leave':
                this.showSystemMessage(`${data.username} покинул канал`);
                break;
            case 'message_deleted':
                this.deleteMessage(data.message_id);
                break;
        }
    }
    
    addMessage(data) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.id = `message-${data.message_id}`;
        
        const avatarUrl = data.avatar || '/media/avatars/default.png';
        const time = data.timestamp ? new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        
        messageElement.innerHTML = `
            <img src="${avatarUrl}" alt="${data.username}" class="message-avatar">
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author" style="color: ${this.getUserColor(data.user_id)}">
                        ${data.username}
                    </span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${this.formatMessage(data.message)}</div>
            </div>
        `;
        
        this.messageContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    showSystemMessage(text) {
        const systemMessage = document.createElement('div');
        systemMessage.classList.add('system-message');
        systemMessage.textContent = text;
        this.messageContainer.appendChild(systemMessage);
        this.scrollToBottom();
    }
    
    showTypingIndicator(username) {
        let indicator = document.getElementById('typingIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'typingIndicator';
            indicator.className = 'typing-indicator active';
            this.messageContainer.appendChild(indicator);
        }
        indicator.textContent = `${username} печатает...`;
        
        setTimeout(() => {
            if (indicator) {
                indicator.remove();
            }
        }, 3000);
    }
    
    clearTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    deleteMessage(messageId) {
        const messageElement = document.getElementById(`message-${messageId}`);
        if (messageElement) {
            messageElement.remove();
        }
    }
    
    async loadOlderMessages() {
        // Загрузка более старых сообщений при прокрутке вверх
        const firstMessage = this.messageContainer.querySelector('.message');
        if (!firstMessage) return;
        
        const messageId = firstMessage.id.replace('message-', '');
        
        try {
            const response = await fetch(`/chat/load-messages/${this.channelId}/?before=${messageId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                const scrollHeight = this.messageContainer.scrollHeight;
                
                data.messages.reverse().forEach(msg => {
                    const messageElement = this.createMessageElement(msg);
                    this.messageContainer.insertBefore(messageElement, firstMessage);
                });
                
                // Сохраняем позицию прокрутки
                this.messageContainer.scrollTop = this.messageContainer.scrollHeight - scrollHeight;
            }
        } catch (error) {
            console.error('Error loading older messages:', error);
        }
    }
    
    createMessageElement(data) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.id = `message-${data.id}`;
        
        const avatarUrl = data.avatar || '/media/avatars/default.png';
        const time = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageElement.innerHTML = `
            <img src="${avatarUrl}" alt="${data.author}" class="message-avatar">
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">${data.author}</span>
                    <span class="message-time">${time}</span>
                    ${data.edited ? '<span class="edited-badge">(изменено)</span>' : ''}
                </div>
                <div class="message-text">${this.formatMessage(data.content)}</div>
            </div>
        `;
        
        return messageElement;
    }
    
    showContextMenu(x, y, messageElement) {
        // Удаляем предыдущее меню
        const existingMenu = document.querySelector('.context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
        
        const messageId = messageElement.id.replace('message-', '');
        const isOwnMessage = messageElement.querySelector('.message-author').textContent.trim() === this.username;
        
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        
        let menuItems = '';
        
        if (isOwnMessage) {
            menuItems += `
                <div class="context-menu-item" onclick="chatManager.editMessage(${messageId})">
                    <i class="fas fa-edit"></i> Редактировать
                </div>
                <div class="context-menu-item danger" onclick="chatManager.deleteMessage(${messageId})">
                    <i class="fas fa-trash"></i> Удалить
                </div>
            `;
        } else {
            menuItems += `
                <div class="context-menu-item" onclick="chatManager.replyToMessage(${messageId})">
                    <i class="fas fa-reply"></i> Ответить
                </div>
                <div class="context-menu-item" onclick="chatManager.copyMessage(${messageId})">
                    <i class="fas fa-copy"></i> Копировать
                </div>
            `;
        }
        
        menu.innerHTML = menuItems;
        document.body.appendChild(menu);
        
        // Закрываем меню при клике вне его
        const closeMenu = (e) => {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 0);
    }
    
    async editMessage(messageId) {
        const newContent = prompt('Редактировать сообщение:');
        if (!newContent) return;
        
        try {
            const response = await fetch(`/chat/edit-message/${messageId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ content: newContent })
            });
            
            if (response.ok) {
                const messageElement = document.getElementById(`message-${messageId}`);
                messageElement.querySelector('.message-text').textContent = newContent;
                
                // Добавляем метку "изменено"
                if (!messageElement.querySelector('.edited-badge')) {
                    const badge = document.createElement('span');
                    badge.className = 'edited-badge';
                    badge.textContent = '(изменено)';
                    messageElement.querySelector('.message-header').appendChild(badge);
                }
            }
        } catch (error) {
            console.error('Error editing message:', error);
        }
    }
    
    async deleteMessage(messageId) {
        if (!confirm('Удалить сообщение?')) return;
        
        try {
            const response = await fetch(`/chat/delete-message/${messageId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                this.socket.send(JSON.stringify({
                    type: 'delete_message',
                    message_id: messageId
                }));
            }
        } catch (error) {
            console.error('Error deleting message:', error);
        }
    }
    
    replyToMessage(messageId) {
        const messageElement = document.getElementById(`message-${messageId}`);
        const author = messageElement.querySelector('.message-author').textContent;
        const text = messageElement.querySelector('.message-text').textContent;
        
        this.messageInput.value = `> ${author}: ${text}\n`;
        this.messageInput.focus();
    }
    
    copyMessage(messageId) {
        const messageElement = document.getElementById(`message-${messageId}`);
        const text = messageElement.querySelector('.message-text').textContent;
        
        navigator.clipboard.writeText(text).then(() => {
            // Показываем уведомление
            this.showNotification('Текст скопирован!');
        });
    }
    
    formatMessage(text) {
        // Форматирование текста (Markdown-подобное)
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
        text = text.replace(/__(.+?)__/g, '<u>$1</u>');
        text = text.replace(/~~(.+?)~~/g, '<s>$1</s>');
        text = text.replace(/`(.+?)`/g, '<code>$1</code>');
        
        // Ссылки
        text = text.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank">$1</a>'
        );
        
        // Эмодзи
        const emojiMap = {
            ':)': '😊',
            ':(': '😢',
            ':D': '😃',
            ';)': '😉',
            '<3': '❤️',
            ':thumbsup:': '👍',
            ':thumbsdown:': '👎',
            ':fire:': '🔥',
        };
        
        for (const [code, emoji] of Object.entries(emojiMap)) {
            text = text.replace(new RegExp(code, 'g'), emoji);
        }
        
        return text;
    }
    
    getUserColor(userId) {
        // Генерируем цвет для пользователя на основе его ID
        const colors = [
            '#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#e74c3c',
            '#f1c40f', '#e67e22', '#1abc9c', '#34495e', '#95a5a6'
        ];
        return colors[userId % colors.length];
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--discord-primary);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            animation: fadeIn 0.3s ease-out;
            z-index: 9999;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 2000);
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }
}

// Инициализация чата при загрузке страницы
let chatManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof channelId !== 'undefined' && typeof userId !== 'undefined' && typeof username !== 'undefined') {
        chatManager = new ChatManager(channelId, userId, username);
    }
});