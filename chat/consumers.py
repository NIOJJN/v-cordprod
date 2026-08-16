import json
import re
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, DirectMessage, Notification
from servers.models import Channel
from accounts.models import User
import uuid


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            message = data.get('message', '')
            channel_id = data.get('channel_id')
            image_data = data.get('image')  # base64 изображение
            
            saved_message = await self.save_message(
                user=self.scope['user'],
                channel_id=channel_id,
                content=message,
                image_data=image_data
            )
            
            if saved_message:
                await self.handle_mentions(message, channel_id, saved_message)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.scope['user'].username,
                    'user_id': self.scope['user'].id,
                    'avatar': self.scope['user'].avatar.url if self.scope['user'].avatar else None,
                    'timestamp': saved_message.timestamp.isoformat() if saved_message else None,
                    'message_id': saved_message.id if saved_message else None,
                    'image_url': saved_message.attachments.url if saved_message and saved_message.attachments else None,
                }
            )
        
        elif message_type == 'delete_message':
            message_id = data.get('message_id')
            await self.delete_message(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'message_deleted', 'message_id': message_id}
            )
        
        elif message_type == 'edit_message':
            message_id = data.get('message_id')
            new_content = data.get('content')
            edited_msg = await self.edit_message(message_id, new_content)
            if edited_msg:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_edited',
                        'message_id': message_id,
                        'content': new_content,
                    }
                )
        
        elif message_type == 'pin_message':
            message_id = data.get('message_id')
            pinned = await self.toggle_pin(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'message_pinned', 'message_id': message_id, 'is_pinned': pinned}
            )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def message_deleted(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def message_edited(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def message_pinned(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def save_message(self, user, channel_id, content, image_data=None):
        try:
            channel = Channel.objects.get(id=channel_id)
            message = Message.objects.create(channel=channel, author=user, content=content or '')
            
            # Сохраняем изображение
            if image_data:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                file = ContentFile(base64.b64decode(imgstr), name=filename)
                message.attachments.save(filename, file)
                message.content = content or '📷 Изображение'
                message.save()
            
            return message
        except Channel.DoesNotExist:
            return None
    
    @database_sync_to_async
    def delete_message(self, message_id):
        try:
            Message.objects.filter(id=message_id, author=self.scope['user']).delete()
        except:
            pass
    
    @database_sync_to_async
    def edit_message(self, message_id, new_content):
        try:
            msg = Message.objects.get(id=message_id, author=self.scope['user'])
            msg.content = new_content
            msg.edited = True
            msg.edited_at = timezone.now()
            msg.save()
            return msg
        except:
            return None
    
    @database_sync_to_async
    def toggle_pin(self, message_id):
        try:
            msg = Message.objects.get(id=message_id)
            msg.is_pinned = not msg.is_pinned
            msg.pinned_at = timezone.now() if msg.is_pinned else None
            msg.save()
            return msg.is_pinned
        except:
            return None
    
    @database_sync_to_async
    def handle_mentions(self, content, channel_id, message):
        if not content:
            return
        mentions = re.findall(r'@(\w+)', content)
        for username in mentions:
            try:
                user = User.objects.get(username=username)
                if user != self.scope['user']:
                    Notification.objects.create(
                        user=user,
                        notification_type='mention',
                        title='Вас упомянули',
                        message=f'{self.scope["user"].username} упомянул вас',
                        link=f'/servers/{message.channel.server.id}/channel/{channel_id}/'
                    )
            except User.DoesNotExist:
                pass


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.other_user_id = int(self.scope['url_route']['kwargs']['user_id'])
        ids = sorted([self.user.id, self.other_user_id])
        self.room_name = f'dm_{ids[0]}_{ids[1]}'
        self.room_group_name = f'dm_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        recipient_id = data['recipient_id']
        image_data = data.get('image')
        
        saved_dm = await self.save_direct_message(
            sender=self.user,
            recipient_id=recipient_id,
            content=message,
            image_data=image_data
        )
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'dm_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'avatar': self.user.avatar.url if self.user.avatar else None,
                'timestamp': saved_dm.timestamp.isoformat() if saved_dm else None,
                'image_url': saved_dm.attachments.url if saved_dm and saved_dm.attachments else None,
            }
        )
    
    async def dm_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def save_direct_message(self, sender, recipient_id, content, image_data=None):
        try:
            recipient = User.objects.get(id=recipient_id)
            dm = DirectMessage.objects.create(sender=sender, recipient=recipient, content=content or '')
            
            if image_data:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                file = ContentFile(base64.b64decode(imgstr), name=filename)
                dm.attachments.save(filename, file)
                dm.content = content or '📷 Изображение'
                dm.save()
            
            return dm
        except User.DoesNotExist:
            return None