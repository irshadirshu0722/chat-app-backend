
import json
# import aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .websocket_manager import get_room_channels, get_channels
from django.utils import timezone
from .models import ChatRoom, UnsentMessages
from django.conf import settings

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.username = await self._get_username()
        self.redis = settings.REDIS_CONNECTION
        await self._set_channel_name()
        self.room_group_name = f"{self.username}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        await self.sent_unsent_message()
        await self.sent_user_status('online')

    async def disconnect(self, close_code):
        await self.sent_user_status('offline')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self._remove_channel_name()
        self.redis.close()
        # await self.redis.wait_closed()

    async def receive(self, text_data):
        try:

            data = json.loads(text_data)
            request_type = data.get('type', None)
            message = data.get('message', None)
            room_id = data.get('room_id', None)
            sender = data.get('sender', None)
            media_type = data.get('media_type', None)
            media_data = data.get('media_data', None)
            signal_data = data.get('signalData', None)
            sent_data = {}
            channel_names = []
            if request_type == 'call_user':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                sent_data = {
                    'type': 'call_user',
                    'sender': self.username,
                    'signal': signal_data,
                    "room_id":room_id
                }
            elif request_type == 'call_accepted':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                sent_data = {
                    'type': 'call_accepted',
                    'sender': self.username,
                    'signal': signal_data,
                    "room_id":room_id
                }
            elif request_type == 'call_hangup':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                sent_data = {
                    'type': 'call_hangup',
                    'sender': self.username,
                    "room_id":room_id
                }
            elif request_type == 'message':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                self.offline_users = offline_users
                sent_data = {
                    "type": request_type,
                    'message': message,
                    'room_id': room_id,
                    'message_date':timezone.now(),
                    "sender":sender,
                }
            elif request_type =='typing':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                self.offline_users = offline_users
                sent_data = {
                    "type": request_type,
                    'message': message,
                    "room_id": room_id,
                    "typing_user":self.scope['user'].username
                }
            if request_type == 'one_to_one_message' or request_type == 'one_to_many_message':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                self.offline_users = offline_users
                sent_data = {
                    "type": request_type,
                    'message': message,
                    'room_id': room_id,
                    "sender":sender,
                    'message_date':str(timezone.now()),
                    'media_type': media_type,
                    'media_data': media_data,
                }
            elif request_type == 'user_typing':
                channel_names, offline_users = await get_room_channels(room_id,self.redis)
                self.offline_users = offline_users
                sent_data = {
                    "type": request_type,
                    'typing_user': self.user.username,
                    'room_id': room_id,
                }
            await self.broadcast_message(sent_data, channel_names)
            message_instance = None
            if request_type == 'one_to_one_message' or request_type == 'one_to_many_message':
                # message_instance = await self.save_message(text_data)
                await self.generate_unsent_message(message, request_type, room_id)
        except Exception as error:
            print(error)
    async def call_user(self, event):
        # This method will be called to send call data
        await self.send(text_data=json.dumps(event))
    async def call_hangup(self, event):
        # This method will be called to send call data
        await self.send(text_data=json.dumps(event))
    async def call_accepted(self, event):
        # This method will be called to send call data
        await self.send(text_data=json.dumps(event))
    async def one_to_one_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def one_to_many_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_status(self, event):
        await self.send(text_data=json.dumps(event))
    async def chat_media(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps(event))
    # async def one_to_many_typing(self, event):
    #     await self.send(text_data=json.dumps(event))

    async def sent_unsent_message(self):
        messages_data, messages = await self.get_unsent_messages()
        for message_data, message_instance in zip(messages_data, messages):
            await self.channel_layer.send(
                self.channel_name, message_data
            )
            await database_sync_to_async(message_instance.delete)()

    async def sent_user_status(self, type):
        contacts = await self.get_user_contacts()
        channels_name, _ = await get_channels(contacts,self.redis)
        if type=='offline':
            sent_data = {
                
                'username': self.user.username,
                'type': 'user_status',
                'status':type,
                'last_seen_date':str(timezone.now())
            }
        else:
            sent_data = {
                
                'username': self.user.username,
                'type': 'user_status',
                'status':type
            }
        await self.broadcast_message(sent_data, channels_name)
    async def broadcast_message(self, data, channel_names):
        for channel in channel_names:
            await self.channel_layer.send(
                channel, data
            )

    @database_sync_to_async
    def get_user_contacts(self):
        user = self.scope['user']
        invited_contacts = ChatRoom.objects.filter(personal__inviter=user).all()
        received_contacts = ChatRoom.objects.filter(personal__invitee=user).all()
        contacts = invited_contacts | received_contacts
        contact_user = set()
        for contact in contacts:
            user = contact.personal.get_second_user(self.scope['user'])
            contact_user.add(user.id)
        return contact_user
    @database_sync_to_async
    def get_unsent_messages(self):
        user = self.scope['user']
        messages = UnsentMessages.objects.filter(sender = user.username).all()
        messages_data = []
        for message in messages:
            messages_data.append({
                'message': message.message,
                'room_id': str(message.room_id),
                'type': message.room_type
            })
        return messages_data, messages

    @database_sync_to_async
    def generate_unsent_message(self, message, message_type, room_id):
        users = self.offline_users
        for username in users:
            if not username:continue
            UnsentMessages.objects.create(message=message, sender=username, room_type=message_type,room_id=room_id)
        self.offline_users = []

    @database_sync_to_async
    def _get_username(self):
        return self.user.username

    @database_sync_to_async
    def _set_channel_name(self):
        self.redis.hset(f"user:{self.user.id}", "channel_name", self.channel_name)
        self.redis.hset(f"user:{self.user.id}", "is_online", 1)
        self.redis.hset(f"user:{self.user.id}", "username", self.user.username)
    @database_sync_to_async
    def _remove_channel_name(self):
        self.redis.hset(f"user:{self.user.id}", "channel_name", "")
        self.redis.hset(f"user:{self.user.id}", "is_online", 0)
        self.redis.hset(f"user:{self.user.id}", "last_seen", str(timezone.now()))
