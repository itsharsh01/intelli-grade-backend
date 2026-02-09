from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from entities.database import get_db
from .service import get_user_service, join_course

router = APIRouter(prefix="/users", tags=["User Management"])

class JoinCourseRequest(BaseModel):
    user_id: int
    course_id: UUID

@router.get("/")
def get_users():
    return get_user_service()

@router.post("/join")
def join_course_endpoint(request: JoinCourseRequest, db: Session = Depends(get_db)):
    """
    Join a course using course_id and user_id.
    """
    return join_course(db, user_id=request.user_id, course_id=request.course_id)
