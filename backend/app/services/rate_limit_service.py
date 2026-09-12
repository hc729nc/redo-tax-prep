from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import DailyUsageModel


class RateLimitExceededError(Exception):
    def __init__(self, kind: str, limit: int):
        self.kind = kind
        self.limit = limit
        super().__init__(f"Daily {kind} limit of {limit} reached")


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _get_or_create_row(db: Session, user_id: UUID) -> DailyUsageModel:
    today = _today_utc()
    row = (
        db.query(DailyUsageModel)
        .filter(DailyUsageModel.user_id == str(user_id), DailyUsageModel.usage_date == today)
        .first()
    )
    if row is None:
        row = DailyUsageModel(id=str(uuid4()), user_id=str(user_id), usage_date=today)
        db.add(row)
        db.flush()
    return row


def check_and_increment_chat_usage(db: Session, user_id: UUID) -> None:
    """Raises RateLimitExceededError without incrementing if already at the limit -
    abuse/cost protection for a publicly reachable deployment, not a feature."""
    limit = get_settings().max_chat_messages_per_day
    row = _get_or_create_row(db, user_id)
    if row.chat_messages_count >= limit:
        db.commit()
        raise RateLimitExceededError("chat message", limit)
    row.chat_messages_count += 1
    db.commit()


def check_and_increment_upload_usage(db: Session, user_id: UUID) -> None:
    limit = get_settings().max_uploads_per_day
    row = _get_or_create_row(db, user_id)
    if row.uploads_count >= limit:
        db.commit()
        raise RateLimitExceededError("document upload", limit)
    row.uploads_count += 1
    db.commit()
