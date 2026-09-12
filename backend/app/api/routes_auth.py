from fastapi import APIRouter, Depends, Request, Response

from app.api.schemas import UserOut
from app.deps import get_auth_provider
from app.repositories.interfaces import AuthProvider
from app.repositories.mock_auth import MOCK_SESSION_TOKEN

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/session", response_model=UserOut)
def create_session(
    request: Request,
    response: Response,
    auth: AuthProvider = Depends(get_auth_provider),
) -> UserOut:
    user = auth.get_current_user(request)
    token = auth.create_session(user)
    response.set_cookie("synthia_session", token, httponly=True)
    return UserOut(id=user.id, display_name=user.display_name, email=user.email)


@router.get("/me", response_model=UserOut)
def get_me(
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
) -> UserOut:
    user = auth.get_current_user(request)
    return UserOut(id=user.id, display_name=user.display_name, email=user.email)
