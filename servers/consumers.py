# servers/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Server, ServerMember, Channel
from accounts.models import User

class ServerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.server_id = self.scope['url_route']['kwargs']['server_id']
        self.server_group_name = f'server_{self.server_id}'
        self.user = self.scope['user']
        
        # Проверяем, является ли пользователь участником сервера
        is_member = await self.check_membership()
        
        if not is_member:
            await self.close()
            return
        
        # Присоединяемся к группе сервера
        await self.channel_layer.group_add(
            self.server_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Уведомляем о подключении пользователя
        await self.channel_layer.group_send(
            self.server_group_name,
            {
                'type': 'user_connected',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
        
        # Обновляем статус пользователя
        await self.update_user_status('online')
    
    async def disconnect(self, close_code):
        # Покидаем группу сервера
        await self.channel_layer.group_discard(
            self.server_group_name,
            self.channel_name
        )
        
        # Уведомляем об отключении
        await self.channel_layer.group_send(
            self.server_group_name,
            {
                'type': 'user_disconnected',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
        
        # Обновляем статус пользователя
        await self.update_user_status('offline')
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'typing':
            await self.channel_layer.group_send(
                self.server_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'channel_id': data.get('channel_id'),
                }
            )
        
        elif message_type == 'voice_state':
            await self.channel_layer.group_send(
                self.server_group_name,
                {
                    'type': 'voice_state_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'channel_id': data.get('channel_id'),
                    'muted': data.get('muted', False),
                    'deafened': data.get('deafened', False),
                }
            )
    
    async def user_connected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_connected',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_disconnected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_disconnected',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'channel_id': event['channel_id'],
        }))
    
    async def voice_state_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'voice_state_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'channel_id': event['channel_id'],
            'muted': event['muted'],
            'deafened': event['deafened'],
        }))
    
    @database_sync_to_async
    def check_membership(self):
        return ServerMember.objects.filter(
            server_id=self.server_id,
            user=self.user
        ).exists()
    
    @database_sync_to_async
    def update_user_status(self, status):
        User.objects.filter(id=self.user.id).update(status=status)