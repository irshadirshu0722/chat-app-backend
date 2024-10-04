from django.db import models
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
import secrets
from django.contrib.auth import get_user_model
from user_auth.model_utils import *
from django.utils import timezone as datetime
from datetime import timedelta
User = get_user_model()

class ChatRoom(models.Model, CreatedUpdatedAtModel):
    room_id = models.CharField(max_length=22, unique=True, editable=False, default=secrets.token_urlsafe(16))
    _last_message_date = models.DateTimeField(default=datetime.now)
    room_type = models.CharField(max_length=20, choices=(('one_to_many', 'Group'), ('one_to_one', 'Personal')))

    def __str__(self):
        return f"{self.room_id} - {self.room_type}"

    @property
    def last_message_date(self):
        last_7_days = datetime.now() - timedelta(days=7)
        current_date = datetime.now().date()
        
        if self._last_message_date.date() == current_date:
            return self._last_message_date.strftime("%I:%M %p")
        elif self._last_message_date >= last_7_days:
            return self._last_message_date.strftime("%A")
        else:
            return self._last_message_date.strftime("%d %m %y") 

class PersonalConf(models.Model,CreatedUpdatedAtModel):
    room = models.OneToOneField(ChatRoom,on_delete=models.CASCADE,related_name='personal')
    ACCEPT_CHOICE = [('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')]
    inviter = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='invited_rooms', null=True)
    invitee = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='received_invitations', null=True)
    blocked_user = models.ForeignKey(User,on_delete=models.SET_NULL,related_name='blocked_list',null=True,blank=True) # who blocked
    status = models.CharField(max_length=20,choices=ACCEPT_CHOICE,default='pending')
    def get_second_user(self,user):
        if self.invitee == user:
            return self.inviter
        return self.invitee
    def get_users(self):
        return [self.invitee,self.inviter]
    def __str__(self) -> str:
        return f"{self.room.room_id} inviter:{self.inviter}  invited:{self.invitee}"

class GroupConf(models.Model,CreatedUpdatedAtModel):
    room = models.OneToOneField(ChatRoom,on_delete=models.CASCADE,related_name='group')
    users = models.ManyToManyField(User,related_name='group_rooms')
    group_name = models.CharField(max_length=255)
    group_profile = CloudinaryField('image',null=True)
    description = models.TextField()
    admins = models.ManyToManyField(User,related_name='admin_groups',blank=True)
    main_admin = models.ForeignKey(User,related_name='main_admin_groups',on_delete=models.SET_NULL,null=True,blank=True)
    @property
    def group_profile_url(self):
        return self.group_profile.url
    
    def __str__(self) -> str:
        return f'Group id -> {self.pk}-> {self.room.room_id}'
    def remove_user(self,user):
        if user == self.main_admin: return 
        # cannot remove the main admin
        if self.users.contains(user):
            self.users.remove(user)
        if self.admins.contains(user):
            self.admins.remove(user)

class UnsentMessages(models.Model):
    message  = models.CharField(max_length=1000)
    sender = models.CharField(max_length=255)
    room_type = models.CharField(max_length=20,choices=[('one_to_many','Group'),('one_to_one','Personal')],default='personal')
    room_id = models.CharField(255)
    def get_user(self):
        return User.objects.get(id=self.user_id)
    def get_room_messgae(self,):
        room = ChatRoom.objects.get(room_id=self.room_id)


