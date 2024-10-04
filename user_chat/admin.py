from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PersonalConf)
admin.site.register(GroupConf)
admin.site.register(ChatRoom)
admin.site.register(UnsentMessages)
