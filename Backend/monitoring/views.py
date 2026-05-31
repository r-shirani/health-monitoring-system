from django.shortcuts import render
from rest_framework import viewsets
from .serializers import VitalSignSerializer, DeviceSerializer
from .models import Device, VitalSign
from django.contrib.auth.decorators import login_required

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
    
@login_required
def dashboard(request):
    user_devices = Device.objects.filter(user=request.user)
    return render(request, 'monitoring/dashboard.html', {'devices' : user_devices})