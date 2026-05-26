# Generated migration for UserProfile model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fullname', models.CharField(blank=True, max_length=100, verbose_name='Họ và tên')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Số điện thoại')),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='Ngày sinh')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Người dùng')),
            ],
            options={
                'verbose_name': 'Hồ sơ người dùng',
                'verbose_name_plural': 'Hồ sơ người dùng',
                'db_table': 'dashboard_userprofile',
                'ordering': ['-created_at'],
            },
        ),
    ]
