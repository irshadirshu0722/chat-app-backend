import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
import uuid
from django.conf import settings
from user_auth.model_utils import *
from cloudinary.models import CloudinaryField

# Create your models here.
class UserManager(BaseUserManager):
  def create_user(self,email,password=None,**extra_fields):
    if not email:
      raise ValueError('Users must have an email address')
    email = self.normalize_email(email)
    user = self.model(email=email,**extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user
  def create_superuser(self,email,password=None,**extra_fields):
    extra_fields.setdefault('is_staff',True)
    extra_fields.setdefault('is_superuser',True)
    self.create_user(email,password,**extra_fields)



class User(AbstractBaseUser,PermissionsMixin):
  email = models.EmailField(unique=True)
  username = models.CharField(max_length=255,unique=True)
  profile = CloudinaryField('image',null=True,blank=True)
  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)
  date_joined = models.DateTimeField(auto_now_add=True)

  objects = UserManager()
  USERNAME_FIELD = 'email'
  
  def __str__(self) :
    return str(self.email) +"=====>"
  @property
  def profile_url(self):
    if self.profile:
      return self.profile.url
    
    return "https://img.freepik.com/premium-photo/stylish-man-flat-vector-profile-picture-ai-generated_606187-310.jpg"



class UserChannel(models.Model):
  user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='channel')
  channel_name = models.CharField(max_length=500,null=True,blank=True)
  is_online = models.BooleanField(default=False)
  # _last_seen = models.DateTimeField(default=datetime.datetime.now())

class AuthToken(models.Model,CreatedUpdatedAtModel):
  token = models.CharField(max_length=500,null=True,blank=True)
  user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='auth_token')
  def __str__(self) :
    return str(self.token) +"===>"+ str(self.user.email)


