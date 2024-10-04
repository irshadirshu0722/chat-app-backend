from jwt.exceptions import ExpiredSignatureError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .tokenAuthentication import JWTAuthentication
from .models import *
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True)

  class Meta:
    model = User
    fields = ('email','password','username',)
    extra_kwargs = {'password':{'write_only':True}}

  def create(self, validated_data):
    user = User.objects.create(email=validated_data['email'],username=validated_data['username'])
    user.set_password(validated_data['password'])
    user.save()
    return user

class LoginSerializer(serializers.Serializer):
  email = serializers.EmailField()
  id = serializers.CharField(max_length=50,read_only=True)
  password = serializers.CharField(max_length=255,write_only=True)
  def validate(self, attrs):
    email = attrs.get('email',None)
    password = attrs.get('password',None)
    if not email:
      raise serializers.ValidationError("An email Address is required for login")
    if not password:
      raise serializers.ValidationError("A password is required for login")
    user = authenticate(username=email,password=password)
    if not user:
      raise serializers.ValidationError("Invalid Email or Password")
    if not user.is_active:
      raise serializers.ValidationError('user is inactive')
    return {
      'email':user.email,
      'id':user.id,
      
      }
  def verify_or_refresh_token(self,validated_data):
    id = validated_data['id']
    user = User.objects.get(id=id)
    if not user.auth_token:
      token = JWTAuthentication().generate_token(validated_data)
      AuthToken.objects.create(user=user,token=token)
    token = user.auth_token.token
    jt =  JWTAuthentication()
    try:
      jt.decode_verify_token(token)
    except ExpiredSignatureError:
      token = jt.generate_token(validated_data)
      token_instance = user.auth_token
      token_instance.token = token
      token_instance.save()
    except Exception as e:
      print(e)
    return {
      'message':'Login successfully',
      'token':token,
      'user':{
      'id':validated_data['id'],
      'email':validated_data['email'],
      'username':user.username
      }
    }

class RoomSearchSerializer(serializers.Serializer):
  search_query = serializers.CharField()



class UserDetailsSerializer(serializers.ModelSerializer):
  profile_image_url = serializers.SerializerMethodField()
  class Meta:
    model = User
    fields = ('username','profile_image_url','id')
  def get_profile_image_url(self,instance):
    try:
      return instance.profile.profile_image_url
    except:
      return settings.DEFAULT_USER_PROFILE


class UserAccessSerializer(serializers.ModelSerializer):
  profile = serializers.SerializerMethodField()
  class Meta:
    model = User
    fields = ('username','id','profile')
  def get_profile(self,instance):
    return instance.profile_url
