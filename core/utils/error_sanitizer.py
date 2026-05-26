import logging
import traceback

logger = logging.getLogger('security')

def sanitize_error(e, is_tech_admin=False):
    """
    Xử lý thông điệp lỗi trước khi hiển thị cho người dùng.
    Nếu là Tech Admin thì hiện chi tiết (DEV_ERROR), ngược lại hiện thông báo chung.
    """
    error_str = str(e)
    
    # Log chi tiết lỗi (bao gồm stack trace) vào log file
    logger.error(f"SYSTEM_EXCEPTION: {error_str}\n{traceback.format_exc()}")
    
    if is_tech_admin:
        return f"DEV_ERROR: {error_str}"
    else:
        # Thông báo thân thiện cho người dùng cuối
        return "Hệ thống đang gặp sự cố kỹ thuật hoặc CSDL đang bận. Vui lòng liên hệ quản trị viên hoặc thử lại sau."
