"""
GreenMind Dashboard - Models
Định nghĩa data structure cho dashboard app
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extend Django User với thông tin bổ sung.
    Thay thế Dim_Users (SQL Server) - không cần dual authentication nữa.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="Người dùng"
    )
    fullname = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Họ và tên"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Số điện thoại"
    )
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Ngày sinh"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ngày cập nhật"
    )
    
    class Meta:
        db_table = 'dashboard_userprofile'
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Hồ sơ người dùng"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.fullname or 'Chưa cập nhật'}"
    
    def get_display_name(self):
        """Trả về tên hiển thị (fullname hoặc username)"""
        return self.fullname or self.user.username


# Signal để tự động tạo UserProfile khi tạo User mới
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Tự động tạo UserProfile khi User được tạo"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Tự động save UserProfile khi User được save"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
