from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.seed_data import USERS, get_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/users")
def list_demo_users() -> list[dict]:
    """Lets the frontend render a 'pick a user' login screen instead of
    asking people to remember five demo accounts."""
    return [
        {
            "username": u.username,
            "full_name": u.full_name,
            "roles": u.roles,
            "department": u.department,
        }
        for u in USERS.values()
    ]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = get_user(payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile(**current_user.public_profile())
