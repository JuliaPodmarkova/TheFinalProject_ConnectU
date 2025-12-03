import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

# Мы убрали отсюда импорты моделей и вызов get_user_model(),
# чтобы избежать ошибки AppRegistryNotReady

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        self.user = self.scope['user']

        # Проверяем, что пользователь аутентифицирован и является участником чата
        is_participant = await self.is_user_participant()
        if not self.user.is_authenticated or not is_participant:
            await self.close()
            return

        # Присоединяемся к группе WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Отключаемся от группы WebSocket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получение сообщения от клиента (WebSocket)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        # Сохраняем сообщение в БД
        new_message = await self.save_message(message_content)

        # Отправляем сообщение всем участникам группы
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', # это вызовет метод chat_message
                'message': new_message.content,
                'sender_id': self.user.id,
                'sender_name': self.user.profile.full_name,
                'sender_avatar_url': self.user.profile.get_avatar_url()
            }
        )

    # Получение сообщения от группы и отправка его клиенту (WebSocket)
    async def chat_message(self, event):
        # Отправляем данные обратно клиенту в формате JSON
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_avatar_url': event['sender_avatar_url']
        }))

    @sync_to_async
    def save_message(self, content):
        # Импортируем модели здесь, чтобы избежать ошибки при запуске
        from .models import Match, Message
        match = Match.objects.get(id=self.match_id)
        # self.user уже доступен благодаря AuthMiddlewareStack
        return Message.objects.create(match=match, sender=self.user, content=content)

    @sync_to_async
    def is_user_participant(self):
        # Импортируем модели здесь, чтобы избежать ошибки при запуске
        from .models import Match
        try:
            match = Match.objects.get(id=self.match_id)
            return self.user == match.user1 or self.user == match.user2
        except Match.DoesNotExist:
            return False
