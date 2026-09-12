from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from app.api.schemas import UserOut
from app.config import get_settings
from app.deps import get_auth_provider
from app.repositories.email_password_auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    EmailAlreadyRegisteredError,
    EmailPasswordAuthProvider,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=SESSION_MAX_AGE_SECONDS,
    )


@router.post("/signup", response_model=UserOut)
def signup(
    body: SignupRequest,
    response: Response,
    auth: EmailPasswordAuthProvider = Depends(get_auth_provider),
) -> UserOut:
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        user = auth.signup(body.email, body.password, body.display_name)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = auth.create_session(user)
    _set_session_cookie(response, token)
    return UserOut(id=user.id, display_name=user.display_name, email=user.email)


@router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    response: Response,
    auth: EmailPasswordAuthProvider = Depends(get_auth_provider),
) -> UserOut:
    try:
        user = auth.login(body.email, body.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = auth.create_session(user)
    _set_session_cookie(response, token)
    return UserOut(id=user.id, display_name=user.display_name, email=user.email)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserOut)
def get_me(
    request: Request,
    auth: EmailPasswordAuthProvider = Depends(get_auth_provider),
) -> UserOut:
    user = auth.get_current_user(request)
    return UserOut(id=user.id, display_name=user.display_name, email=user.email)
