// static/js/server.js
class ServerManager {
    constructor(serverId, userId) {
        this.serverId = serverId;
        this.userId = userId;
        this.socket = null;
        this.init();
    }
    
    init() {
        if (!this.serverId) return;
        this.connectWebSocket();
        this.setupEventListeners();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = new WebSocket(
            `${protocol}//${window.location.host}/ws/server/${this.serverId}/`
        );
        
        this.socket.onopen = () => {
            console.log('Server WebSocket connected');
        };
        
        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleServerEvent(data);
        };
        
        this.socket.onclose = () => {
            console.log('Server WebSocket disconnected, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }
    
    setupEventListeners() {
        // Переключение категорий
        document.querySelectorAll('.category-header').forEach(header => {
            header.addEventListener('click', () => {
                const category = header.parentElement;
                const channels = category.querySelectorAll('.channel');
                const icon = header.querySelector('i');
                
                channels.forEach(channel => {
                    channel.style.display = channel.style.display === 'none' ? 'block' : 'none';
                });
                
                icon.classList.toggle('fa-chevron-down');
                icon.classList.toggle('fa-chevron-right');
            });
        });
        
        // Создание сервера
        const createServerBtn = document.querySelector('.add-server');
        if (createServerBtn) {
            createServerBtn.addEventListener('click', () => {
                this.showCreateServerModal();
            });
        }
        
        // Присоединение к серверу
        const joinServerBtn = document.getElementById('joinServerBtn');
        if (joinServerBtn) {
            joinServerBtn.addEventListener('click', () => {
                this.showJoinServerModal();
            });
        }
    }
    
    handleServerEvent(data) {
        switch (data.type) {
            case 'user_connected':
                this.userConnected(data);
                break;
            case 'user_disconnected':
                this.userDisconnected(data);
                break;
            case 'user_typing':
                this.showUserTyping(data);
                break;
            case 'voice_state_update':
                this.updateVoiceState(data);
                break;
        }
    }
    
    userConnected(data) {
        const memberElement = document.querySelector(`.member[data-user-id="${data.user_id}"]`);
        if (memberElement) {
            memberElement.querySelector('.member-name').classList.add('online');
        }
        
        // Показываем системное сообщение в текущем канале
        if (chatManager) {
            chatManager.showSystemMessage(`${data.username} подключился к серверу`);
        }
    }
    
    userDisconnected(data) {
        const memberElement = document.querySelector(`.member[data-user-id="${data.user_id}"]`);
        if (memberElement) {
            memberElement.querySelector('.member-name').classList.remove('online');
        }
        
        if (chatManager) {
            chatManager.showSystemMessage(`${data.username} отключился от сервера`);
        }
    }
    
    showUserTyping(data) {
        // Показываем индикатор печати в соответствующем канале
        if (chatManager && data.channel_id === chatManager.channelId) {
            chatManager.showTypingIndicator(data.username);
        }
    }
    
    updateVoiceState(data) {
        // Обновляем состояние голосового канала
        console.log(`${data.username} voice state:`, data);
    }
    
    showCreateServerModal() {
        const modal = document.getElementById('createServerModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }
    
    showJoinServerModal() {
        const modal = document.getElementById('joinServerModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }
    
    async createChannel(channelData) {
        try {
            const response = await fetch(`/servers/${this.serverId}/create_channel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(channelData)
            });
            
            const data = await response.json();
            if (data.success) {
                location.reload();
            }
        } catch (error) {
            console.error('Error creating channel:', error);
        }
    }
    
    async inviteUser(userId) {
        try {
            const response = await fetch(`/servers/${this.serverId}/invite/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ user_id: userId })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Приглашение отправлено!');
            }
        } catch (error) {
            console.error('Error inviting user:', error);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Инициализация менеджера сервера
let serverManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof serverId !== 'undefined' && typeof userId !== 'undefined') {
        serverManager = new ServerManager(serverId, userId);
    }
});