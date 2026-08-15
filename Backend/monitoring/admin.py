# from django.contrib import admin
# from .models import VitalSign, Device
# from rest_framework.authtoken.admin import TokenAdmin
# from rest_framework.authtoken.models import Token

# admin.site.register(Device)
# admin.site.register(VitalSign)

# #temp
# try:
#     admin.site.unregister(Token)
#     TokenAdmin.raw_id_fields = ['user']
#     admin.site.register(Token, TokenAdmin)
# except:
#     pass


from django.contrib import admin
from .models import Device, VitalSign


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
  # افزودن id عددی دیتابیس در کنار سایر فیلدها
  list_display = (
      'id',
      'device_id',
      'get_user_id',
      'user',
      'name',
      'is_active',
      'created_at',
  )
  search_fields = ('device_id', 'user__username', 'name')
  list_filter = ('is_active', 'created_at')

  # متد نمایش آیدی عددی کاربر متصل به دستگاه
  @admin.display(description='User ID')
  def get_user_id(self, obj):
    return obj.user.id if obj.user else '-'


@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'get_device_id_text',
      'heart_rate',
      'oxygen_level',
      'timestamp',
  )
  list_filter = ('timestamp', 'device')

  @admin.display(description='Device String ID')
  def get_device_id_text(self, obj):
    return obj.device.device_id if obj.device else '-'