

from django.urls import path
from .views import *

urlpatterns = [
    path('personal-room-connection/<str:username>/', ContactsConnection.as_view(), name='check-personal-connection'),
    path('accept-personal-room/',AcceptRoom.as_view(),name='accept-room'),
    path('group-room-connection-create/',GroupRoomConnectionCreate.as_view(),name='group-room-connection-create'),
    path('group-room-connection-update/<str:room_id>/',GroupRoomConnectionUpdate.as_view(),name='group-room-connection-get-join-exit'),
    path('group-room-admin-control/<str:room_id>/<str:username>/',GroupRoomAdminControl.as_view(),name='group-room-admin-control'),
    path('group-room-admin-user-control/<str:room_id>/<str:username>/',GroupRoomAdminUserControl.as_view(),name='group-room-admin-user-control'),
    # path('search/',RoomSearch.as_view(),name='search-room'),
    path('',GetRooms.as_view(),name='get-all-room'),
    path('personal-room-update/',PersonalRoomConnectionUpdate.as_view(),name='personal-room-connection-update'),
    path('room-details/<str:room_id>',GetRoomDetails.as_view(),name='room-details'),
]