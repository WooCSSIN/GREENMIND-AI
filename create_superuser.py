#!/usr/bin/env python
"""
🔑 GreenMind AI — Quick Superuser Setup Script
Chạy file này để tạo tài khoản superuser kỹ thuật ngay lập tức.
Cách dùng: python create_superuser.py
"""
import os
import sys
import django

# ─── Setup Django ───
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User, Group

# ─── Config ───
SUPERUSER_USERNAME = "admin"
SUPERUSER_PASSWORD = "greenmind2026"
SUPERUSER_EMAIL    = "admin@greenmind.ai"

TECH_USERNAME = "tech_admin"
TECH_PASSWORD = "tech2026"

print("\n" + "="*60)
print("  🌱 GREENMIND AI — Account Provisioning Utility")
print("="*60)

# 1. Tạo hoặc cập nhật Superuser
try:
    if User.objects.filter(username=SUPERUSER_USERNAME).exists():
        u = User.objects.get(username=SUPERUSER_USERNAME)
        u.set_password(SUPERUSER_PASSWORD)
        u.is_superuser = True
        u.is_staff = True
        u.save()
        print(f"  ✅ SUPERUSER đã tồn tại → Cập nhật mật khẩu: {SUPERUSER_USERNAME}")
    else:
        User.objects.create_superuser(
            username=SUPERUSER_USERNAME,
            password=SUPERUSER_PASSWORD,
            email=SUPERUSER_EMAIL
        )
        print(f"  ✅ SUPERUSER mới: {SUPERUSER_USERNAME}")
except Exception as e:
    print(f"  ❌ Lỗi tạo superuser: {e}")

# 2. Tạo group Technical và user kỹ thuật
try:
    tech_group, _ = Group.objects.get_or_create(name='Technical')
    print(f"  ✅ Group 'Technical' sẵn sàng.")
    
    if not User.objects.filter(username=TECH_USERNAME).exists():
        tech_user = User.objects.create_user(
            username=TECH_USERNAME,
            password=TECH_PASSWORD
        )
        tech_user.groups.add(tech_group)
        tech_user.save()
        print(f"  ✅ TECH USER mới: {TECH_USERNAME}")
    else:
        tech_user = User.objects.get(username=TECH_USERNAME)
        tech_user.groups.add(tech_group)
        tech_user.set_password(TECH_PASSWORD)
        tech_user.save()
        print(f"  ✅ TECH USER cập nhật: {TECH_USERNAME}")
except Exception as e:
    print(f"  ⚠️  Tech group: {e}")

# 3. Tạo group Admin
try:
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    print(f"  ✅ Group 'Admin' sẵn sàng.")
except Exception as e:
    print(f"  ⚠️  Admin group: {e}")

print("\n" + "─"*60)
print("  📋 THÔNG TIN ĐĂNG NHẬP:")
print(f"  ► Superuser : {SUPERUSER_USERNAME} / {SUPERUSER_PASSWORD}")
print(f"    (Truy cập mọi trang, kể cả Health Check + Django Admin)")
print(f"  ► Tech Admin: {TECH_USERNAME} / {TECH_PASSWORD}")
print(f"    (Truy cập Health Check, nhưng không có quyền Admin CRUD)")
print("─"*60)
print(f"  🌐 URL: http://127.0.0.1:8000/")
print(f"  🔧 Admin Panel: http://127.0.0.1:8000/admin/")
print(f"  🏥 Health Check: http://127.0.0.1:8000/dashboard/health-check/")
print("="*60 + "\n")
