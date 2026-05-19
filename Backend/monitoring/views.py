from django.shortcuts import render
from rest_framework import viewsets
from .serializers import VitalSignSerializer, DeviceSerializer
from .models import Device, VitalSign

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

class VitalSignViewSet(viewsets.ModelViewSet):
    queryset = VitalSign.objects.all()
    serializer_class = VitalSignSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('device')
        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)

        return queryset