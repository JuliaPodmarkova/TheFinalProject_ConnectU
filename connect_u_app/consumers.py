import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Match, Message
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_match(self, match_id):
        try:
            return Match.objects.select_related('user1', 'user2').get(id=match_id)
        except Match.DoesNotExist:
            return None

    # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
    # Теперь метод создает сообщение и сразу возвращает словарь с данными
    @database_sync_to_async
    def create_message_and_get_data(self, content):
        new_message = Message.objects.create(
            match=self.match,
            sender=self.user,
            content=content
        )
        # Получаем все нужные данные здесь, в синхронном контексте
        return {
            'content': new_message.content,
            'timestamp': new_message.get_formatted_timestamp(),
            'sender_name': self.user.profile.full_name,  # Заодно и имя получим здесь же
        }

    # Метод get_sender_name больше не нужен, но пусть пока останется на всякий случай
    @database_sync_to_async
    def get_sender_name(self):
        return self.user.profile.full_name

    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group_name = f'chat_{self.match_id}'
        self.user = self.scope['user']

        self.match = await self.get_match(self.match_id)

        if self.user.is_authenticated and self.match and (
                self.user.id == self.match.user1.id or self.user.id == self.match.user2.id):
            await self.channel_layer.group_add(
                self.match_group_name,
                self.channel_name
            )
            await self.accept()
            logger.warning(
                f"USER {self.user.id} CONNECTED to group {self.match_group_name}")  # Используем warning, чтобы было видно
        else:
            await self.close()

    async def disconnect(self, close_code):
        logger.warning(f"USER {self.user.id} DISCONNECTED from group {self.match_group_name}")
        await self.channel_layer.group_discard(
            self.match_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        logger.warning(
            f"RECEIVED message '{message_content}' from USER {self.user.id} for group {self.match_group_name}")

        message_data = await self.create_message_and_get_data(content=message_content)

        await self.channel_layer.group_send(
            self.match_group_name,
            {
                'type': 'chat_message',
                'message': message_data['content'],
                'sender_id': self.user.id,
                'sender_name': message_data['sender_name'],
                'timestamp': message_data['timestamp'],
            }
        )
        logger.warning(f"SENT message to channel layer for group {self.match_group_name}")

    async def chat_message(self, event):
        logger.warning(f"CONSUMER for USER {self.user.id} GOT message from channel layer: {event}")

        message = event['message']
        sender_id = event['sender_id']
        sender_name = event['sender_name']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'timestamp': timestamp
        }))
        logger.warning(f"SENT message via websocket to USER {self.user.id}")