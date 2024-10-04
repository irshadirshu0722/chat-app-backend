import traceback
import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from channels.db import database_sync_to_async
User = get_user_model()
class JWTAuthentication(BaseAuthentication):
    @staticmethod
    def generate_token(payload):
        expiration = datetime.now() + timedelta(days=settings.AUTH_TOKEN_EXPIRES_DAY)
        payload['exp'] = expiration
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY, algorithm="HS256")
        return token
    def decode_verify_token(self,token):
        payload =jwt.decode(token, key=settings.SECRET_KEY, algorithms=["HS256"])
        self.verify_token(payload)
    def verify_token(self, payload):
        if 'exp' not in payload:
            raise DecodeError("Token has no expiration")
        exp_timestamp = payload['exp']
        current_timestamp =datetime.now().timestamp()
        if current_timestamp > exp_timestamp:
            raise ExpiredSignatureError('Token has expired')
    @database_sync_to_async
    def authenticate_websocket(self, scope,token):
        try:
            if not token:
                raise ExpiredSignatureError()
            
            payload = jwt.decode(token,key=settings.SECRET_KEY,algorithms=['HS256'])
            self.verify_token(payload)
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            return user
        except (DecodeError, ExpiredSignatureError, User.DoesNotExist) as e:
            traceback.print_exc()
            raise AuthenticationFailed("Expired or Invalid Token")
    def authenticate(self, request):
        token = self.extract_token(request=request)
        if token is None:
            return None
        try:
            payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms=["HS256"])
            self.verify_token(payload=payload)
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            return (user, None)
        except (DecodeError, ExpiredSignatureError, User.DoesNotExist) as e:
            traceback.print_exc()
            raise AuthenticationFailed("Expired or Invalid Token")
    def extract_token(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(' ')[1]
        return None
