"""
GreenMind Public API - v1
Module: Permissions (Phân quyền theo vai trò)

Vai trò (Role) được đọc từ Django Groups:
  - 'Admin'   : Toàn quyền (CRUD catalog, chạy simulator, đọc mọi API)
  - 'Manager' : Đọc dashboard, forecast, esg. Không có quyền ghi.
  - 'Viewer'  : Chỉ đọc báo cáo ESG công khai.

Nếu user chưa thuộc group nào => mặc định coi là 'Viewer'.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Chỉ dành cho thành viên group 'Admin'."""
    message = "Yêu cầu quyền Admin để thực hiện thao tác này."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.groups.filter(name="Admin").exists() or request.user.is_superuser)
        )


class IsManagerOrAbove(BasePermission):
    """Dành cho Admin và Manager."""
    message = "Yêu cầu quyền Manager hoặc Admin."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_superuser or
            request.user.groups.filter(name__in=["Admin", "Manager"]).exists()
        )


class IsAnyAuthenticatedUser(BasePermission):
    """Mọi user đã đăng nhập đều được truy cập (kể cả Viewer)."""
    message = "Yêu cầu đăng nhập."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
