from rest_framework import serializers
from .models import Device, VitalSign

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('device_id', 'user', 'name', 'created_at', 'is_active', 'id',)
        read_only_fields = ('created_at',)

class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = ('device', 'heart_rate', 'oxygen_level', 'timestamp', 'id',)
        read_only_fields = ('timestamp',)