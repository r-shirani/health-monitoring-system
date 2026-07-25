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
from .tasks import send_async_critical_alert
from django.http import HttpResponse
from django.db.models import Avg, Max, Min
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from .reports import generate_vital_signs_pdf

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
                    
                    device.last_email_sent = now
                    device.save()
                    
                    send_async_critical_alert.delay(
                        email_target=emergency_email,
                        device_name=device.name,
                        heart_rate=heart_rate,
                        oxygen_level=oxygen_level,
                        timestamp=vital_sign.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    print("[DJANGO] Critical data received! Task offloaded to Celery. Response sent to hardware immediately.")
    
@login_required
def dashboard(request):
    user_devices = Device.objects.filter(user=request.user)
    return render(request, 'monitoring/dashboard.html', {'devices' : user_devices})

@login_required
def generate_report_pdf(request):
    date_range = request.GET.get('range', 'today')
    device_id_req = request.GET.get('device')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    now = timezone.now()
    start_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_filter = now
    
    if start_date and end_date:
        try:
            start_filter = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            end_filter = timezone.datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            date_range = 'custom'
        except ValueError:
            pass
    elif date_range == 'week':
        start_filter = now - timedelta(days=7)
    elif date_range == 'month':
        start_filter = now - timedelta(days=30)

    if device_id_req:
        device = Device.objects.filter(id=device_id_req, user=request.user).first()
    else:
        device = Device.objects.filter(user=request.user).first()

    if not device:
        return HttpResponse("No device found!", status=404)
        
    vitals = VitalSign.objects.filter(
        device=device, 
        timestamp__range=[start_filter, end_filter]
    ).order_by('-timestamp')

    stats = vitals.aggregate(
        avg_hr=Avg('heart_rate'), max_hr=Max('heart_rate'), min_hr=Min('heart_rate'),
        avg_ox=Avg('oxygen_level'), max_ox=Max('oxygen_level'), min_ox=Min('oxygen_level')
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="medical_report_{date_range}.pdf"'

    generate_vital_signs_pdf(
        response_stream=response,
        device=device,
        user=request.user,
        vitals=vitals,
        stats=stats,
        date_range=date_range,
        start_filter=start_filter,
        end_filter=end_filter,
        now=now
    )

    return response