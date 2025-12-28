from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class OtpCode(models.Model):
    code = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    purpose = models.CharField(
        max_length=20,
        choices=[('reset', 'Password Reset'), ('signup', 'Signup Verification')],
        default='reset'
    )
    used = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='otp_codes')

    def __str__(self):
        return f"{self.user.username} - {self.purpose}"