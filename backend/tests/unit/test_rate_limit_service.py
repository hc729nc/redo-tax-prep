from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services.rate_limit_service import (
    RateLimitExceededError,
    check_and_increment_chat_usage,
    check_and_increment_upload_usage,
)


@pytest.fixture
def db_session():
    from app.db import models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_chat_usage_allowed_under_limit(db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "max_chat_messages_per_day", 3)
    user_id = uuid4()
    check_and_increment_chat_usage(db_session, user_id)
    check_and_increment_chat_usage(db_session, user_id)
    check_and_increment_chat_usage(db_session, user_id)  # 3rd call still allowed (limit=3)


def test_chat_usage_blocked_once_limit_reached(db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "max_chat_messages_per_day", 2)
    user_id = uuid4()
    check_and_increment_chat_usage(db_session, user_id)
    check_and_increment_chat_usage(db_session, user_id)
    with pytest.raises(RateLimitExceededError):
        check_and_increment_chat_usage(db_session, user_id)


def test_upload_usage_tracked_separately_from_chat_usage(db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "max_uploads_per_day", 1)
    monkeypatch.setattr(config.get_settings(), "max_chat_messages_per_day", 5)
    user_id = uuid4()
    check_and_increment_upload_usage(db_session, user_id)
    with pytest.raises(RateLimitExceededError):
        check_and_increment_upload_usage(db_session, user_id)
    # Chat usage for the same user is unaffected by hitting the upload limit.
    check_and_increment_chat_usage(db_session, user_id)


def test_usage_is_per_user(db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "max_chat_messages_per_day", 1)
    user_a = uuid4()
    user_b = uuid4()
    check_and_increment_chat_usage(db_session, user_a)
    with pytest.raises(RateLimitExceededError):
        check_and_increment_chat_usage(db_session, user_a)
    check_and_increment_chat_usage(db_session, user_b)  # different user, own quota
