import traceback
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated
from user_chat.serializers import RoomsGetSerializer

from user_auth.serializers import  UserDetailsSerializer,RoomSearchSerializer
from user_chat.serializers import GroupRoomSerializer
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from user_chat.models import  ChatRoom
from django.contrib.postgres.search import SearchVector

# Create your views here.
User = get_user_model()




# class RoomSearch(APIView):
#   permission_classes = [IsAuthenticated]
#   def post(self,request):
#     serializer = RoomSearchSerializer(data=request.data)
#     try:
#       if serializer.is_valid(raise_exception=True):
#         search_query = serializer.validated_data['search_query']
#         if not search_query:
#           return Response({'global_users':[],'global_groups':[]},status=status.HTTP_200_OK)
#         filter_global_users = User.objects.filter(username__startswith=search_query).exclude(request.user).all()
#         filter_global_group  = GroupRoom.objects.annotate(search=SearchVector('name')).filter(search = search_query).exclude(request.user)
#         users_data =PersonalRoomUserSerializer(filter_global_users,many=True).data
#         group_data =GroupRoomSerializer(filter_global_group,many=True).data
#         return Response({'users':users_data,'groups':group_data})
#     except Exception as e:
#       traceback.print_exc()
#       return Response(status=status.HTTP_400_BAD_REQUEST)
    
# class GetUserRoomDetails(APIView):
#   permission_classes = [IsAuthenticated]
#   def get(self,request,id):
#     try:
#       user = User.objects.get(id=id)
#       user_data = UserDetailsSerializer(user).data
#       user_data['name'] = user_data['first_name'] +" "+user_data['last_name']
#       del user_data['first_name'] ,user_data['last_name'] ,user_data['username']
#       res = {'header_details':user_data}
#       is_room_exist = ChatRoom.objects.filter(personal__inviter__in=(user.id,second_user.id),personal__invitee__in=(user.id,second_user.id)).first()
#       res['has_connection'] = True if is_room_exist else False
#       if is_room_exist:
#         res['room'] = RoomsGetSerializer(room).data      
#       return Response(res,status=status.HTTP_200_OK)
#     except Exception as e: 
#       traceback.print_exc()
#       return Response(status=status.HTTP_400_BAD_REQUEST)
      

      
