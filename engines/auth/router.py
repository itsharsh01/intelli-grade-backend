from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from entities.database import get_db
from .schemas import LoginRequest, RegisterRequest, TokenResponse
from .service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Sign in with email and password. Use remember_me=true for 30-day token."""
    return login_user(
        db,
        email=body.email,
        password=body.password,
        remember_me=body.remember_me,
    )


@router.post("/register", response_model=TokenResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Create account and return token. Use this to create demo user alex@example.com with password lumina2024."""
    return register_user(db, email=body.email, password=body.password)
