from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from entities.database import get_db
from .service import get_module_content
from uuid import UUID

router = APIRouter(prefix="/content-loading", tags=["Content Loading Engine"])

@router.get("/{module_id}")
def get_content(module_id: UUID, db: Session = Depends(get_db)):
    content = get_module_content(db, module_id)
    if not content:
        raise HTTPException(status_code=404, detail="Module content not found")
    return content
