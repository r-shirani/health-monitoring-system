from django.contrib import admin
from .models import VitalSign, Device

admin.site.register(Device)
admin.site.register(VitalSign)
