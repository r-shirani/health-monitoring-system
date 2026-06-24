from django.shortcuts import render
from rest_framework import viewsets
from .serializers import VitalSignSerializer, DeviceSerializer
from .models import Device, VitalSign
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from .email import EmergencyEmailService
from django.utils import timezone
from datetime import timedelta

class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VitalSignViewSet(viewsets.ModelViewSet):
    queryset = VitalSign.objects.all().order_by('-timestamp')
    serializer_class = VitalSignSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(device__user=self.request.user)
        device_id = self.request.query_params.get('device')
        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)

        return queryset
    
    def perform_create(self, serializer):
        vital_sign = serializer.save()
        device = vital_sign.device
        emergency_email = device.emergency_email if hasattr(device, 'emergency_email') else None

        if emergency_email:
            heart_rate = vital_sign.heart_rate
            oxygen_level = vital_sign.oxygen_level

            if heart_rate > 120 or heart_rate < 50 or oxygen_level < 92:
                now = timezone.now()

                if device.last_email_sent is None or (now - device.last_email_sent) > timedelta(minutes=5):  
                    device.last_email_sent = timezone.now() 
                    device.save()

                    EmergencyEmailService.send_critical_alert(
                        email_target= emergency_email,
                        device_name= device.name,
                        heart_rate= heart_rate,
                        oxygen_level= oxygen_level,
                        timestamp= vital_sign.timestamp
                    )
    
@login_required
def dashboard(request):
    user_devices = Device.objects.filter(user=request.user)
    return render(request, 'monitoring/dashboard.html', {'devices' : user_devices})