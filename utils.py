import secrets
import re

def generate_api_key():
    return secrets.token_urlsafe(32)

def is_valid_regex(pattern: str) -> bool:
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

def log_action(session, user_id: int | None, action: str, details: str):
    from .models import AuditLog
    log = AuditLog(user_id=user_id, action=action, details=details)
    session.add(log)
    session.commit()