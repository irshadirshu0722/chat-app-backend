import traceback
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated

from .serializers import   UserSerializer,LoginSerializer
from user_chat.serializers import GroupRoomSerializer
from rest_framework import status
from user_auth.tokenAuthentication import JWTAuthentication
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector

User = get_user_model()
@api_view(['POST'])
def register_user(request):
  serializer = UserSerializer(data=request.data)
  try:
    if serializer.is_valid(raise_exception=True):
      serializer.save()
      return Response(serializer.data,status=status.HTTP_201_CREATED)
  except Exception as e:
    traceback.print_exc()
    return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def login_user(request):
  serializer = LoginSerializer(data=request.data)
  try:
    if serializer.is_valid(raise_exception=True):
      data = serializer.verify_or_refresh_token(serializer.validated_data)
      return Response(data,status=status.HTTP_201_CREATED)
  except Exception as e:
    traceback.print_exc()
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    return Response({'username': request.user.username}, status=status.HTTP_200_OK)

