from rest_framework import serializers
from .models import ChatRoom,PersonalConf,GroupConf
from user_auth.serializers import UserAccessSerializer
from django.contrib.auth import get_user_model
from user_auth.serializers import UserDetailsSerializer

from django.conf import settings
User = get_user_model()



class GroupRoomSerializer(serializers.ModelSerializer):
  users  = serializers.SerializerMethodField()
  class Meta:
    model = GroupConf
    fields = ('group_name','group_profile_url','description',"users")
  def get_users(self,instance):
    users = instance.users.all()
    admins = instance.admins.all()
    main_admin = instance.main_admin
    users_data = {}
    print(admins)
    for user in users:
      data=UserDetailsSerializer(user).data
      data['is_admin'] = user in admins
      data['is_main_admin'] = user==main_admin
      users_data[user.id] = data
    return users_data

class PersonalRoomSerializer(serializers.ModelSerializer):
  inviter = UserAccessSerializer()
  invitee = UserAccessSerializer()
  blocked_user = UserAccessSerializer()
  class Meta:
    model = PersonalConf
    fields = ('invitee','inviter','blocked_user','status',)
  

class RoomsGetSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField()
    personal = serializers.SerializerMethodField()
    # last_message_date = serializers.SerializerMethodField()
    class Meta:
        model = ChatRoom
        fields = ('last_message_date', 'room_id','room_type','group','personal')
    # def get_last_message_date(self, instance):
    #    return instance.last_message_date
    def get_group(self, instance):
        try:
            return GroupRoomSerializer(instance.group).data
        except GroupConf.DoesNotExist:
            return None
    def get_personal(self, instance):
        try:
            return PersonalRoomSerializer(instance.personal).data
        except PersonalConf.DoesNotExist:
            return None
    def to_representation(self, instance):
      data =  super().to_representation(instance)
      current_user = self.context.get('user')
      title = 'None'
      if data['personal']:
        user1 = data['personal']['invitee']
        user2 = data['personal']['inviter']
        title = user1['username'] if user1['username'] !=current_user.username else user2['username']
        profile = user1['profile'] if user1['username'] !=current_user.username else user2['profile']
      else:
        title = data['group']['group_name']
        profile = data['group']['group_profile_url']
      data['display_details'] = {
        "title":title,
        "profile":profile
      }
      return data

class GroupCreateSerializer(serializers.ModelSerializer):
  users = serializers.ListField()
  class Meta:
    model = GroupConf
    fields = '__all__'
    read_only_fields = ('admins','room','created_at','updated_at','users','messages','main_admin',)
    extra_kwargs = {'main_admin':{'required':False}}
  def save(self, **kwargs):
    current_user = self.context.get('current_user')
    users = self.validated_data.pop('users',[])
    room = ChatRoom.objects.create(room_type='one_to_many')
    self.validated_data['room'] = room
    instance =  super().save()
    users_instance = User.objects.filter(username__in=users).all()
    room_users = []
    for user in users_instance:
      instance.users.add(user.id)
      room_users.append(user.id)
    instance.users.add(current_user.id)
    room_users.append(current_user.id)
    instance.main_admin = current_user
    instance.save()
    return instance,room_users

