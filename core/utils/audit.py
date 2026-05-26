from sqlalchemy import text
import logging

logger = logging.getLogger('security')

def _resolve_sql_user_id(conn, django_user_id):
    """Ánh xạ Django User sang SQL Server UserID."""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=django_user_id)
        row = conn.execute(text("SELECT UserID FROM Dim_Users WHERE Username=:u"), {"u": user.username}).fetchone()
        if row: return row[0]
        fallback = conn.execute(text("SELECT TOP 1 UserID FROM Dim_Users WHERE Role='Admin' ORDER BY UserID ASC")).fetchone()
        return fallback[0] if fallback else 1
    except:
        return 1

def log_audit_action(engine, user_id, action, table_name=None, record_id=None, old_value=None, new_value=None, ip_address=None):
    """
    Ghi log thao tác quản trị xuống SQL Server và log file.
    """
    try:
        with engine.begin() as conn:
            sql_uid = _resolve_sql_user_id(conn, user_id)
            conn.execute(text(
                "INSERT INTO Admin_Action_Logs (UserID, Action, TableName, RecordID, OldValue, NewValue, IPAddress) "
                "VALUES (:uid, :act, :tbl, :rid, :old, :new, :ip)"
            ), {
                "uid": sql_uid,
                "act": action,
                "tbl": table_name,
                "rid": record_id,
                "old": str(old_value) if old_value else None,
                "new": str(new_value) if new_value else None,
                "ip": ip_address
            })
        
        logger.warning(f"AUDIT_TRAIL: User={sql_uid} Action={action} Table={table_name} ID={record_id} IP={ip_address}")
        
    except Exception as e:
        logger.error(f"AUDIT_LOG_ERROR: {str(e)}")
