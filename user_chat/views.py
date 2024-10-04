import traceback
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework import status
from user_chat.models import *
from .serializers import *
from user_auth.serializers import RoomSearchSerializer
from django.contrib.postgres.search import SearchVector
from django.db.models import Case, When, F, Value, IntegerField,CharField,BooleanField
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce

from django.conf import settings
import json
User = get_user_model()
redis = settings.REDIS_CONNECTION

class ContactsConnection(APIView):
  """
  get : This is used to check does user has a connection with given user
  post : Used to create a connection or room
  """
  permission_classes = [IsAuthenticated]
  def get(self,request,username):
    user = request.user
    try:
      second_user = User.objects.get(username=username)
      has_connection  = ChatRoom.objects.filter(personal__inviter__in=(user.id,second_user.id),personal__invitee__in=(user.id,second_user.id)).first()
      if not has_connection:
        return Response(UserDetailsSerializer(second_user).data,status=status.HTTP_404_NOT_FOUND)
      room_data = PersonalRoomSerializer(has_connection.personal).data
      room_data['ui_data'] = UserDetailsSerializer(second_user).data
      return Response(room_data,status=status.HTTP_200_OK)
    except Exception as error:
      traceback.print_exc()
      return Response({'message':str(error)},status=status.HTTP_400_BAD_REQUEST)
  def post(self,request,username):
    user = request.user
    second_user = User.objects.get(username=username)
    if not second_user:return Response(status=status.HTTP_404_NOT_FOUND)
    if second_user==user:return Response(status=status.HTTP_400_BAD_REQUEST)
    has_connection  = ChatRoom.objects.filter(personal__inviter__in=(user.id,second_user.id),personal__invitee__in=(user.id,second_user.id)).first()
    if has_connection : return Response(status=status.HTTP_409_CONFLICT)
    try:
      room = ChatRoom.objects.create()
      personal_chat_room = PersonalConf.objects.create(room = room,inviter=user,invitee=second_user)
      redis.hset("rooms",f"{room.room_id}",json.dumps([user.id,second_user.id]))
      return Response(RoomsGetSerializer(personal_chat_room).data,status=status.HTTP_200_OK)
    except Exception as error:
      return Response({'message':str(error)},status=status.HTTP_400_BAD_REQUEST)

class AcceptRoom(APIView):
  """
  post : Used to accept a personal room request
  """
  permission_classes = [IsAuthenticated]
  def post(self,request):
    room_id = request.data.get('room_id')
    st = request.data.get('status')
    room = ChatRoom.objects.get(room_id=room_id)

    if not room : return Response(status=status.HTTP_404_NOT_FOUND)
    room = room.personal
    if room.inviter == request.user :return Response(status=status.HTTP_403_FORBIDDEN)
    if st not in ['pending','accepted','rejected'] :return  Response(status=status.HTTP_400_BAD_REQUEST)
    room.status = st
    room.save()
    return Response(status=status.HTTP_200_OK)

class PersonalRoomConnectionUpdate(APIView):
  # put is used to block and unblock
  def put(self,request):
    try:
      user = request.user
      room_id = request.data.get('room_id')
      type = request.data.get('type')
      room = ChatRoom.objects.get(room_id=room_id)
      
      personal_room  = room.personal
      if user != personal_room.inviter and  user!= personal_room.invitee:
        return Response(status=status.HTTP_403_FORBIDDEN)
      if type =='block':
        personal_room.blocked_user = user
      elif type=='unblock':
        personal_room.blocked_user = None
      else:
         return Response(status=status.HTTP_400_BAD_REQUEST)
      personal_room.save()
      return Response()
    except ChatRoom.DoesNotExist:
      return Response({'error':"chat room not found"},status=status.HTTP_404_NOT_FOUND)
    except :
      traceback.print_exc()
      return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class GroupRoomConnectionCreate(APIView):
  """
  post : used to create room
  """
  permission_classes =[IsAuthenticated]
  def post(self,request):
    user = request.user
    serializer = GroupCreateSerializer(data=request.data,context={'current_user':user})
    try:
      if serializer.is_valid(raise_exception=True):
        instance,room_users = serializer.save(user=user)
        redis.hset("rooms",f"{instance.room.room_id}",json.dumps(room_users))
        return Response(GroupRoomSerializer(instance).data,status=status.HTTP_201_CREATED)
    except Exception as error:
      traceback.print_exc()
      return Response({'message':str(error)},status=status.HTTP_400_BAD_REQUEST)


class GroupRoomConnectionUpdate(APIView):
    """
    get : used to get the group details 
    post : used to join room
    put: exit from group
    delete : remove user
    """
    permission_classes = [IsAuthenticated]

    def get_room(self, room_id):
        try:
            return ChatRoom.objects.get(room_id=room_id)
        except ChatRoom.DoesNotExist:
            return None

    def get(self, request, room_id):
        room = self.get_room(room_id)
        if not room:return Response(status=status.HTTP_404_NOT_FOUND)
        room = room.group
        return Response(GroupRoomSerializer(room).data, status=status.HTTP_200_OK)
    def post(self, request, room_id):
        room = self.get_room(room_id)
        if not room:return Response(status=status.HTTP_404_NOT_FOUND)
        room = room.group
        if room.users.filter(id=request.user.id).exists():
            return Response(status=status.HTTP_409_CONFLICT)
        room.users.add(request.user)
        room.save()
        return Response(GroupRoomSerializer(room).data, status=status.HTTP_200_OK)
    def delete(self, request, room_id):
        room = self.get_room(room_id)
        if not room:
            return Response(status=status.HTTP_404_NOT_FOUND)
        room = room.group
        room.remove_user(request.user)
        room.save()
        return Response(GroupRoomSerializer(room).data, status=status.HTTP_200_OK)

class GroupRoomAdminControl(APIView):
  """
  post : add new admin to group
  put : change main admin
  delete : remove admin
  """
  permission_classes = [IsAuthenticated]

  def get_room(self, room_id):
        try:
            return ChatRoom.objects.get(room_id=room_id)
        except ChatRoom.DoesNotExist:
            return None
  def post(self,request,room_id,username):
    room = self.get_room(room_id)
    if not room:return Response(status=status.HTTP_404_NOT_FOUND)
    room = room.group
    access_user = User.objects.get(username=username)
    if not access_user :return Response(status=status.HTTP_404_NOT_FOUND)

    #  checking the user is in admins or main admin
    if not room.admins.contains(request.user) and not room.main_admin == request.user: return Response(status=status.HTTP_403_FORBIDDEN)

    if not room.users.contains(access_user) or not room.users.contains(request.user) :return Response(status=status.HTTP_404_NOT_FOUND)

    room.admins.add(access_user)
    room.save()
    return Response(status=status.HTTP_200_OK)
  def delete(self,request,room_id,username):
    room = self.get_room(room_id)
    if not room:return Response(status=status.HTTP_404_NOT_FOUND)
    room = room.group
    access_user = User.objects.get(username=username)
    if not access_user :return Response(status=status.HTTP_404_NOT_FOUND)
    if not room.admins.contains(request.user) and not room.main_admin == request.user: return Response(status=status.HTTP_403_FORBIDDEN)

    if not room.users.contains(access_user) or not room.users.contains(request.user) :return Response(status=status.HTTP_404_NOT_FOUND)

    if room.admins.contains(access_user):
      room.admins.remove(access_user)
      room.save()
    return Response(status=status.HTTP_200_OK)
  def put(self,request,room_id,username):
    room = self.get_room(room_id)
    if not room:return Response(status=status.HTTP_404_NOT_FOUND)
    room = room.group
    access_user = User.objects.get(username=username)
    if not access_user :return Response(status=status.HTTP_404_NOT_FOUND)

    if not room.users.contains(access_user) or not room.users.contains(request.user) :return Response(status=status.HTTP_404_NOT_FOUND)
    if not room.main_admin == request.user: return Response(status=status.HTTP_403_FORBIDDEN)
    if room.admins.contains(access_user):
      room.admins.remove(access_user)
    room.main_admin = access_user 
    room.save()
    return Response(status=status.HTTP_200_OK)

class GroupRoomAdminUserControl(APIView):
  """
  used to adding the user by admin and removing
  """
  permission_classes = [IsAuthenticated]
  def get_room(self, room_id):
        try:
            return ChatRoom.objects.get(room_id=room_id)
        except ChatRoom.DoesNotExist:
            return None
  def post(self,request,room_id,username):
      room = self.get_room(room_id)
      if not room:return Response({"message":'room not exist'},status=status.HTTP_404_NOT_FOUND)
      room = room.group
      access_user = User.objects.get(username=username)
      if not access_user :return Response({"message":'user not exist'},status=status.HTTP_404_NOT_FOUND)
      #  checking the user is in admins or main admin
      if not room.admins.contains(request.user) and not room.main_admin == request.user: return Response(status=status.HTTP_403_FORBIDDEN)
      if room.users.contains(access_user) : return Response(status=status.HTTP_409_CONFLICT)
      room.users.add(access_user)
      room.save()
      return Response(status=status.HTTP_200_OK)
  def delete(self,request,room_id,username):
      room = self.get_room(room_id)
      if not room:return Response(status=status.HTTP_404_NOT_FOUND)
      room = room.group
      access_user = User.objects.get(username=username)
      if not access_user :return Response(status=status.HTTP_404_NOT_FOUND)
      #  checking the user is in admins or main admin
      if not room.admins.contains(request.user) and not room.main_admin == request.user: return Response(status=status.HTTP_403_FORBIDDEN)
      if not room.users.contains(access_user) :return Response(status=status.HTTP_404_NOT_FOUND)
      if not room.users.contains(access_user) : return Response(status=status.HTTP_409_CONFLICT)

      room.remove_user(access_user)
      room.save()
      return Response(status=status.HTTP_200_OK)


# class RoomSearch(APIView):
#   permission_classes = [IsAuthenticated]
#   def post(self,request):
#     print('hi')
#     serializer = RoomSearchSerializer(data=request.data)
#     try:
#       if serializer.is_valid(raise_exception=True):
#         search_query = serializer.validated_data['search_query']
#         if not search_query:
#           return Response({'global_users':[],'global_groups':[]},status=status.HTTP_200_OK)
#         current_user_persona_rooms = PersonalRoom.objects.annotate(
#             first_user_id=Case(
#                 When(invitee=request.user, then=F('invitee__id')),
#                 When(inviter=request.user, then=F('inviter__id')),
#                 output_field=IntegerField()
#             ),second_user_id=Case(
#                 When(invitee=request.user, then=F('inviter__id')),
#                 When(inviter=request.user, then=F('invitee__id')),
#                 output_field=IntegerField()
#             )).filter(first_user_id=request.user.id).values_list('second_user_id',flat=True)
#         filter_global_users = User.objects.annotate(has_in_ids = Case(
#           When(id__in=current_user_persona_rooms,then=Value(True)),
#           default=False,
#           output_field=BooleanField()
#           )).filter(username__startswith=search_query,has_in_ids=False).exclude(id=request.user.id).all()

#         filter_global_group  = GroupRoom.objects.annotate(search=SearchVector('group_name','description')).filter(search = search_query).exclude(users__in=[request.user.id]).all()
#         filter_my__group  = GroupRoom.objects.annotate(search=SearchVector('group_name','description')).filter(search = search_query,users__in=[request.user.id]).all()
#         filter_my_contacts = PersonalRoom.objects.annotate(
#             contact_user=Case(
#                 When(invitee=request.user, then=F('inviter__username')),
#                 When(inviter=request.user, then=F('invitee__username')),
#                 output_field=CharField()
#             )
#               ).filter(
#                   contact_user__startswith=search_query
#               ).all()
#         my_contacts_data = PersonalRoomDetailSerializer(filter_my_contacts,many=True,context={'user':request.user}).data
#         my_groups_data = GroupRoomSerializer(filter_my__group,many=True).data
#         users_data = UserDetailsSerializer(filter_global_users,many=True).data
#         group_data = GroupRoomSerializer(filter_global_group,many=True).data
#         return Response({'global_contacts':users_data,'global_groups':group_data,'my_groups':my_groups_data,'my_contacts':my_contacts_data})
#     except Exception as e:
#       traceback.print_exc()
#       return Response(status=status.HTTP_400_BAD_REQUEST)


class GetRooms(APIView):
  permission_classes = [IsAuthenticated]
  def get(self,request):
    groups = ChatRoom.objects.filter(group__users=request.user).all()
    contacts = ChatRoom.objects.annotate(invitee = F('personal__invitee'),
                                        inviter = F('personal__inviter')).annotate(
            check_user=Case(
                When(invitee=request.user.id, then=True),
                When(inviter=request.user.id, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).filter(check_user=True).all()
    rooms = groups | contacts
    rooms = rooms.order_by('-_last_message_date')
    data = RoomsGetSerializer(rooms,many=True,context={'user':request.user}).data
    return Response(data,status=status.HTTP_200_OK)



class GetRoomDetails(APIView):
  permission_classes = [IsAuthenticated]

  def get(self,request,room_id):
    room = ChatRoom.objects.get(room_id=room_id)
    if(not room_id ) : return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(RoomsGetSerializer(room,context={'user':request.user}).data)


class SaveMediaView(APIView):
  

  def post(self,request):
    pass





