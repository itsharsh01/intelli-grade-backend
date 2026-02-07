from fastapi import APIRouter
from .service import get_user_service

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/")
def get_users():
    return get_user_service()
