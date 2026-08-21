from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, VitalSignViewSet, dashboard, generate_report_pdf
from django.contrib.auth import views as auth_views
from . import views


router = DefaultRouter()

router.register(r'devices', DeviceViewSet, basename='devices')
router.register(r'vitals', VitalSignViewSet, basename='vitalSign')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='monitoring/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/report/', generate_report_pdf, name='generate_report_pdf'),
    path('api/analyze-ai-range/', views.analyze_range_ai, name='analyze_ai_range'),
    path('api/analyze-ai-session/', views.analyze_last_session_ai, name='analyze_ai_session'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-emergency/', views.update_emergency_contact, name='update_emergency_contact'),
]