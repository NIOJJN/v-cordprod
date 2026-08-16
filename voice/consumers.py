import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import VoiceChannel, VoiceConnection
from servers.models import Channel
from accounts.models import User


class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group_name = f'voice_{self.channel_id}'
        self.user = self.scope['user']
        
        voice_channel = await self.get_or_create_voice_channel()
        await self.connect_user(voice_channel)
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Отправляем список подключённых пользователей
        users = await self.get_connected_users_list()
        await self.send(text_data=json.dumps({'type': 'connected_users', 'users': users}))
        
        # Уведомляем всех о новом пользователе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
    
    async def disconnect(self, close_code):
        await self.disconnect_user()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        
        if msg_type == 'offer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'sdp': data['sdp'],
                    'from_user_id': self.user.id,
                    'from_username': self.user.username,
                }
            )
        
        elif msg_type == 'answer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'sdp': data['sdp'],
                    'from_user_id': self.user.id,
                }
            )
        
        elif msg_type == 'ice_candidate':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_ice',
                    'candidate': data['candidate'],
                    'from_user_id': self.user.id,
                }
            )
        
        elif msg_type == 'mute':
            await self.toggle_mute(data.get('muted', False))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_muted',
                    'user_id': self.user.id,
                    'muted': data.get('muted', False),
                }
            )
        
        elif msg_type == 'speaking':
            await self.toggle_speaking(data.get('speaking', False))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_speaking',
                    'user_id': self.user.id,
                    'speaking': data.get('speaking', False),
                }
            )
    
    # Обработчики событий группы
    async def user_joined(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
        }))
    
    async def user_muted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_muted',
            'user_id': event['user_id'],
            'muted': event['muted'],
        }))
    
    async def user_speaking(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_speaking',
            'user_id': event['user_id'],
            'speaking': event['speaking'],
        }))
    
    async def webrtc_offer(self, event):
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'sdp': event['sdp'],
                'from_user_id': event['from_user_id'],
                'from_username': event['from_username'],
            }))
    
    async def webrtc_answer(self, event):
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'sdp': event['sdp'],
                'from_user_id': event['from_user_id'],
            }))
    
    async def webrtc_ice(self, event):
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'from_user_id': event['from_user_id'],
            }))
    
    # База данных
    @database_sync_to_async
    def get_or_create_voice_channel(self):
        channel = Channel.objects.get(id=self.channel_id)
        vc, _ = VoiceChannel.objects.get_or_create(channel=channel)
        return vc
    
    @database_sync_to_async
    def connect_user(self, vc):
        VoiceConnection.objects.get_or_create(user=self.user, voice_channel=vc)
    
    @database_sync_to_async
    def disconnect_user(self):
        VoiceConnection.objects.filter(user=self.user, voice_channel__channel_id=self.channel_id).delete()
    
    @database_sync_to_async
    def get_connected_users_list(self):
        """Возвращает список пользователей в голосовом канале"""
        connections = VoiceConnection.objects.filter(
            voice_channel__channel_id=self.channel_id
        ).select_related('user')
        
        return [
            {
                'user_id': c.user.id,
                'username': c.user.username,
                'is_muted': c.is_muted,
                'is_speaking': c.is_speaking,
            }
            for c in connections
        ]
    
    @database_sync_to_async
    def toggle_mute(self, muted):
        VoiceConnection.objects.filter(
            user=self.user,
            voice_channel__channel_id=self.channel_id
        ).update(is_muted=muted)
    
    @database_sync_to_async
    def toggle_speaking(self, speaking):
        VoiceConnection.objects.filter(
            user=self.user,
            voice_channel__channel_id=self.channel_id
        ).update(is_speaking=speaking)