import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Match, ChatMessage, User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        self.user = self.scope['user']

        if self.user.is_authenticated:
            # Проверка, что пользователь является участником этого мэтча
            is_participant = await self.check_match_participant()
            if is_participant:
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.accept()
            else:
                await self.close(code=403)  # Forbidden
        else:
            await self.close(code=401)  # Unauthorized

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Сохранение сообщения в БД
        await self.save_message(message)

        # Отправка сообщения в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'message': message, 'sender': self.user.id}
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender']

        # Отправка сообщения обратно в WebSocket
        await self.send(text_data=json.dumps({'message': message, 'sender': sender_id}))

    @sync_to_async
    def check_match_participant(self):
        return Match.objects.filter(id=self.match_id, user1=self.user).exists() or \
            Match.objects.filter(id=self.match_id, user2=self.user).exists()

    @sync_to_async
    def save_message(self, message):
        match = Match.objects.get(id=self.match_id)
        ChatMessage.objects.create(match=match, sender=self.user, content=message)