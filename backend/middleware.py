from channels.middleware import BaseMiddleware
from rest_framework.exceptions import AuthenticationFailed
from django.db import close_old_connections
from user_auth.tokenAuthentication import JWTAuthentication
from urllib.parse import parse_qs

class JWTWebsocketMiddleware(BaseMiddleware):
  async def __call__(self, scope, receive, send):
    close_old_connections()
    query_params = parse_qs(scope['query_string'].decode('utf-8'))
    token = query_params.get('token', [None])[0]
    if token is None:
      await send({
        'type':'websocket.close',
        'code':4000
      })
    authenitcation = JWTAuthentication()
    try:
      user = await authenitcation.authenticate_websocket(scope,token)
      if user is not None:
        scope['user'] = user
      else:
        await send({
        'type':'websocket.close',
        'code':4000
      })
      return await super().__call__(scope,receive,send)
    except AuthenticationFailed:
      await  send({
        'type':'websocket.close',
        'code':4002,
      })
      