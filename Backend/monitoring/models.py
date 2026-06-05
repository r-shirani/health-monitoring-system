from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    emergency_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.device_id} {self.user.username}"

class VitalSign(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    heart_rate = models.FloatField(null=True, blank=True)
    oxygen_level = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_id} {self.heart_rate} {self.oxygen_level} {self.timestamp}"