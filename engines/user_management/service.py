from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from entities.models import CourseUser, Course, User

def get_user_service():
    return {"message": "User Management Service Response"}

def join_course(db: Session, user_id: int, course_id: UUID):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check if already joined
    existing = db.query(CourseUser).filter(
        CourseUser.user_id == user_id, 
        CourseUser.course_id == course_id
    ).first()
    
    if existing:
        return {"message": "User already enrolled in this course", "status": "already_joined"}
        
    # Join
    new_entry = CourseUser(user_id=user_id, course_id=course_id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"message": "Successfully joined the course", "status": "success", "entry_id": str(new_entry.id)}
