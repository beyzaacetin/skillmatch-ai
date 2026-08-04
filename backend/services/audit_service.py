from sqlalchemy.orm import Session
import models
from config import settings

class AuditService:
    @staticmethod
    def log(
        db: Session,
        user: models.User | None,
        action: str,
        target_type: str,
        target_id: int | None,
        details: dict = None,
        ip_address: str | None = None
    ):
        if not settings.ENABLE_AUDIT_LOGGING:
            return None
        
        user_id = user.id if user else None
        user_name = user.full_name if user else "System"
        
        log_entry = models.ImmutableAuditLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

audit_service = AuditService()
