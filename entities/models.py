from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text, func, ForeignKey, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1) 
    
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class ModuleContent(Base):
    __tablename__ = "module_content"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    content = Column(String, nullable=True)
    title = Column(String, nullable=True)

class Score(Base):
    __tablename__ = "scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module_content_id = Column(UUID(as_uuid=True), ForeignKey("module_content.id"), nullable=True, index=True)
    
    # Store explicit weight for weighted average
    weight = Column(Float, nullable=False, default=1.0)
    score_type = Column(String, nullable=False) # 'conversation', 'evaluation', etc.
    
    # Score Components
    correctness = Column(Float, nullable=False)
    conceptual_depth = Column(Float, nullable=False)
    reasoning_quality = Column(Float, nullable=False)
    confidence_alignment = Column(Float, nullable=False)
    
    # Metadata
    misconceptions = Column(ARRAY(String), nullable=True)
    feedback = Column(String, nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
