from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import UserModel
from app.domain.entities import User
from app.repositories.interfaces import AuthProvider

DEV_USER_EMAIL = "dev@synthia.local"
MOCK_SESSION_TOKEN = "mock-session-token"


class MockAuthProvider(AuthProvider):
    """No real identity provider yet: always resolves to one seeded dev user.

    Swapping to Cognito/real sessions later only means replacing this class -
    callers only ever see the abstract `AuthProvider` interface.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_dev_user(self) -> UserModel:
        m = self.db.query(UserModel).filter(UserModel.email == DEV_USER_EMAIL).first()
        if m is not None:
            return m
        m = UserModel(id=str(uuid4()), display_name="Dev User", email=DEV_USER_EMAIL)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def get_current_user(self, request: Request) -> User:
        m = self._get_or_create_dev_user()
        return User(id=UUID(m.id), display_name=m.display_name, email=m.email, created_at=m.created_at)

    def create_session(self, user: User) -> str:
        return MOCK_SESSION_TOKEN
