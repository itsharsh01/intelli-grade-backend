from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from entities.models import User
from core.security import verify_password, hash_password, create_access_token


def login_user(db: Session, email: str, password: str, remember_me: bool = False) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if getattr(user, "is_active", 1) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        remember_me=remember_me,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email},
    }


def register_user(db: Session, email: str, password: str) -> dict:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        remember_me=False,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email},
    }
