from django.shortcuts import render
from rest_framework import viewsets
from .serializers import VitalSignSerializer, DeviceSerializer
from .models import Device, VitalSign
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.utils import timezone
from datetime import timedelta
from .tasks import send_async_critical_alert
from django.http import HttpResponse
from django.db.models import Avg, Max, Min
from .reports import generate_vital_signs_pdf
from django.http import JsonResponse
from .ai_service import analyze_vitals_with_ai
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User

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
    pagination_class = None

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
                        device_name=device.name or device.device_id,
                        heart_rate=heart_rate,
                        oxygen_level=oxygen_level,
                        timestamp=vital_sign.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    print("[DJANGO] Critical data received! Task offloaded to Celery. Response sent to hardware immediately.")
    
@login_required
def dashboard(request):
    user_device = Device.objects.filter(user=request.user).first()
    return render(request, 'monitoring/dashboard.html', {'device': user_device})

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

@login_required
def analyze_range_ai(request):
    date_range = request.GET.get('range', 'today')
    device_id_req = request.GET.get('device')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    now = timezone.now()
    start_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_filter = now

    if date_range == 'custom' and start_date and end_date:
        try:
            start_filter = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            end_filter = timezone.datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
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
        return JsonResponse({'status': 'no_device', 'analysis': None}, status=404)

    vitals_qs = VitalSign.objects.filter(device=device, timestamp__range=[start_filter, end_filter]).order_by('timestamp')
    total_count = vitals_qs.count()

    if total_count == 0:
        return JsonResponse({'status': 'empty', 'analysis': None})

    # sampling to prevent maximum reached Token error
    MAX_SAMPLES = 200
    if total_count > MAX_SAMPLES:
        step = total_count // MAX_SAMPLES
        vitals = list(vitals_qs[::step])[:MAX_SAMPLES]
    else:
        vitals = list(vitals_qs)

    csv_lines = ["timestamp,heart_rate,oxygen_level"]
    for v in vitals:
        csv_lines.append(f"{v.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{v.heart_rate},{v.oxygen_level}")
    vitals_csv_text = "\n".join(csv_lines)

    analysis_dict = analyze_vitals_with_ai(vitals_csv_text, is_session=False)
    return JsonResponse({'status': 'success', 'analysis': analysis_dict})

@login_required
def analyze_last_session_ai(request):
    device_id = request.GET.get('device')

    if device_id:
        device = Device.objects.filter(id=device_id, user=request.user).first()
    else:
        device = Device.objects.filter(user=request.user).first()

    if not device:
        return JsonResponse({'status': 'no_device_selected', 'analysis': None}, status=400)

    vitals = VitalSign.objects.filter(device=device).order_by('-timestamp')[:20]
    if not vitals.exists():
        return JsonResponse({'status': 'empty', 'analysis': None})

    csv_lines = ["timestamp,heart_rate,oxygen_level"]
    for v in reversed(vitals):
        csv_lines.append(f"{v.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{v.heart_rate},{v.oxygen_level}")
    vitals_csv_text = "\n".join(csv_lines)

    analysis_dict = analyze_vitals_with_ai(vitals_csv_text, is_session=True)
    return JsonResponse({'status': 'success', 'analysis': analysis_dict})

@login_required
def update_profile(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        user = request.user

        lang = request.COOKIES.get('app_lang', 'fa')
        
        # check the currunt password
        if not user.check_password(old_password):
            msg = "رمز عبور فعلی اشتباه است." if lang == 'fa' else "Current password is incorrect."
            messages.error(request, msg)
            return redirect('dashboard')
            
        # check the username
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                msg = "نام کاربری قبلا انتخاب شده است." if lang == 'fa' else "Username is already taken."
                messages.error(request, msg)
                return redirect('dashboard')
            user.username = new_username
            
        # check the new password
        if new_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            msg = "رمز عبور با موفقیت تغییر یافت." if lang == 'fa' else "Password changed successfully."
            messages.success(request, msg)
        else:
            user.save()
            msg = "تغییرات با موفقیت ثبت شد." if lang == 'fa' else "User profile updated successfully."
            messages.success(request, msg)
            
    return redirect('dashboard')

@login_required
def update_emergency_contact(request):
    if request.method == 'POST':
        emergency_email = request.POST.get('emergency_email')
        lang = request.COOKIES.get('app_lang', 'fa')
        device_id = request.POST.get('device_id')

        device = None
        if device_id and device_id.isdigit():
            device = Device.objects.filter(id=int(device_id), user=request.user).first()

        if not device:
            device = Device.objects.filter(user=request.user).first()

        if device and emergency_email:
            device.emergency_email = emergency_email
            device.save()
            msg = "ایمیل اضطراری با موفقیت ثبت شد." if lang == 'fa' else "Emergency email registered successfully."
            messages.success(request, msg)
        else:
            msg = "لطفا یک ایمیل معتبر وارد کنید." if lang == 'fa' else "Please enter a valid email address."
            messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
            
    return redirect('dashboard')