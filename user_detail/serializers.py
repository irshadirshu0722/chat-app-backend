from rest_framework import serializers
from user_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()





  # def check_room_exist(self,request_user,recieved_user):
  #   instance = PersonalChatRoom.objects.filter(users=(request_user.id,recieved_user.id)).first()
  #   if instance:
  #     return True,PersonalChatRoomDetail(instance).data
  #   return False,{}

  # def create_room(self,request_user,recieved_user):
  #   PersonalChatRoom.objects.create(
  #     users= (request_user.id,recieved_user.id),
  #     requested_user = request_user,)

