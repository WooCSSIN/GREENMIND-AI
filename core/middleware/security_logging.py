import logging
import time
from django.utils.timezone import now

logger = logging.getLogger('security')

class SecurityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Trước khi xử lý request
        start_time = time.time()
        
        # Lấy thông tin client
        ip_address = self.get_client_ip(request)
        user = request.user.username if request.user.is_authenticated else "Anonymous"
        path = request.path
        method = request.method

        response = self.get_response(request)

        # Sau khi xử lý request
        duration = time.time() - start_time
        status_code = response.status_code

        # Log mọi API call (với đường dẫn bắt đầu bằng /api/)
        if path.startswith('/api/'):
            logger.info(
                f"API_CALL: IP={ip_address} User={user} Method={method} Path={path} Status={status_code} Duration={duration:.2f}s"
            )

        # Log failed login attempts
        if path == '/login/' and method == 'POST' and status_code == 200:
            # Trong Django, nếu login thất bại thường quay về trang login với status 200 (chứa error message)
            # Tuy nhiên, cách tốt nhất là kiểm tra xem user có authenticated thành công không
            # Ở đây chúng ta kiểm tra nếu request.user vẫn là anonymous sau POST /login/
            # Lưu ý: request.user được set bởi AuthenticationMiddleware trước khi vào đây
            # Nhưng middleware này chạy sau. Chúng ta cần check kĩ hơn.
            # Đơn giản nhất: Ghi nhận mọi POST /login/ có status 200 (thường là lỗi validation)
            # hoặc check messages nếu possible.
            pass # Sẽ hoàn thiện thêm nếu cần

        # Log Admin actions (Catalog & Simulator POST)
        if (path.startswith('/catalog/') or path.startswith('/simulator/')) and method == 'POST':
            if status_code in [200, 302]: # Thành công hoặc redirect
                logger.warning(
                    f"ADMIN_ACTION: IP={ip_address} User={user} Action={path} Status={status_code}"
                )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
