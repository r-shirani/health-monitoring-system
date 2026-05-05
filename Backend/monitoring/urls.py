from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, VitalSignViewSet

router = DefaultRouter()

router.register(r'devices', DeviceViewSet)
router.register(r'vitals', VitalSignViewSet)

urlpatterns = [
    path('', include(router.urls)),
]