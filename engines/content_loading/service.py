from sqlalchemy.orm import Session
from uuid import UUID
from entities.models import ModuleContent

def get_module_content(db: Session, module_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.id == module_id).first()
