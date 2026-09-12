from __future__ import annotations

from uuid import UUID, uuid4

import bcrypt
from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import UserModel
from app.domain.entities import User
from app.repositories.interfaces import AuthProvider

SESSION_COOKIE_NAME = "synthia_session"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt="synthia-session")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _model_to_user(m: UserModel) -> User:
    return User(id=UUID(m.id), display_name=m.display_name, email=m.email, created_at=m.created_at)


class EmailPasswordAuthProvider(AuthProvider):
    """Real per-user accounts behind email + password, with a signed, timed cookie
    session (no server-side session table to manage/expire). Deliberately simple -
    no email verification, no password reset flow - appropriate for a small public
    demo, not a production identity system."""

    def __init__(self, db: Session):
        self.db = db

    def signup(self, email: str, password: str, display_name: str) -> User:
        email = email.strip().lower()
        existing = self.db.query(UserModel).filter(UserModel.email == email).first()
        if existing is not None:
            raise EmailAlreadyRegisteredError(email)

        m = UserModel(
            id=str(uuid4()),
            display_name=display_name or email.split("@")[0],
            email=email,
            password_hash=_hash_password(password),
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _model_to_user(m)

    def login(self, email: str, password: str) -> User:
        email = email.strip().lower()
        m = self.db.query(UserModel).filter(UserModel.email == email).first()
        if m is None or m.password_hash is None or not _verify_password(password, m.password_hash):
            raise InvalidCredentialsError(email)
        return _model_to_user(m)

    def get_current_user(self, request: Request) -> User:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
        try:
            user_id = _serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
        except (BadSignature, SignatureExpired):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        m = self.db.get(UserModel, user_id)
        if m is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return _model_to_user(m)

    def create_session(self, user: User) -> str:
        return _serializer().dumps(str(user.id))
