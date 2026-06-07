from django.contrib import admin
from .models import VitalSign, Device
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token

admin.site.register(Device)
admin.site.register(VitalSign)

#temp
try:
    admin.site.unregister(Token)
    TokenAdmin.raw_id_fields = ['user']
    admin.site.register(Token, TokenAdmin)
except:
    pass