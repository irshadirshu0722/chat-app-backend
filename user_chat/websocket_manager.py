import json
import traceback
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom
User = get_user_model()



@database_sync_to_async
def get_channels(users,redis):
    channel_names = []
    offline_users = []
    for user_id in users:
        try:
            channel_name = redis.hget(f"user:{user_id}", "channel_name")
            is_online = redis.hget(f"user:{user_id}", "is_online")
            if is_online and is_online.decode('utf-8') == '1':
                channel_names.append(channel_name.decode('utf-8'))
            else:
                offline_users.append(user_id)
        except Exception as e:
            print('Error retrieving channel:', str(e))
    return channel_names, offline_users
@database_sync_to_async
def get_room_channels(room_id,redis):
  room_users = json.loads(redis.hget("rooms",f"{room_id}") or '{}')
  if not room_users:
    return  [],[]
  channel_names = []
  offline_users = []
  for user_id in room_users:
      try:
          channel_name = redis.hget(f"user:{user_id}", "channel_name")
          is_online = redis.hget(f"user:{user_id}", "is_online")
          username = redis.hget(f"user:{user_id}", "username")
          if is_online and is_online.decode('utf-8')=='1':
              channel_names.append(channel_name.decode('utf-8'))
          else:
              offline_users.append(username)
      except Exception as e:
          print('Error retrieving channel:', str(e))
  return channel_names,offline_users

