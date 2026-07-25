from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, VitalSignViewSet, dashboard, generate_report_pdf
from django.contrib.auth import views as auth_views


router = DefaultRouter()

router.register(r'devices', DeviceViewSet, basename='devices')
router.register(r'vitals', VitalSignViewSet, basename='vitalSign')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='monitoring/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/report/', generate_report_pdf, name='generate_report_pdf'),
]