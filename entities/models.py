from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text, func, Numeric, Text, ForeignKey
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text, func, ForeignKey, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import JSON
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
    module_context = Column(JSON, nullable=True)
    title = Column(String, nullable=True)


class UserModuleCompletion(Base):
    """Tracks when a user explicitly marks a module as complete (unlocks quiz)."""
    __tablename__ = "user_module_completion"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    module_id = Column(UUID(as_uuid=True), primary_key=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


# ---------------------------------------------------------------------------
# Quiz & Assessment models (question bank, sessions, attempts, evaluation)
# ---------------------------------------------------------------------------

class Question(Base):
    """
    Pre-stored question in the question bank, organized by module.
    options and correct_answer are JSON for flexibility (MCQ list, DOUBLE_MCQ list of sets, etc.).
    evaluation_rubric is used only for SUBJECTIVE questions by the AI evaluator.
    """
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    module_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question_type = Column(String(32), nullable=False)  # MCQ | DOUBLE_MCQ | SUBJECTIVE
    difficulty = Column(String(16), nullable=False)    # easy | medium | hard
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)               # e.g. ["A", "B", "C", "D"] for MCQ
    correct_answer = Column(JSON, nullable=True)        # single value for MCQ, list for DOUBLE_MCQ, null for SUBJECTIVE
    evaluation_rubric = Column(JSON, nullable=True)     # only for SUBJECTIVE; used by AI
    concept_tags = Column(JSON, nullable=True)          # array of strings, e.g. ["algebra", "equations"]
    weight = Column(Numeric(5, 2), default=1.0, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class QuizSession(Base):
    """
    One quiz attempt per user per module. question_ids are fixed at start so the
    session is deterministic and auditable.
    """
    __tablename__ = "quiz_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(Integer, nullable=False, index=True)
    module_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question_ids = Column(JSON, nullable=False)         # array of question UUIDs, order fixed for this session
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)


class QuestionAttempt(Base):
    """
    One record per question answered in a quiz session. user_answer is the raw
    submission; evaluation is stored in EvaluationResult.
    """
    __tablename__ = "question_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    quiz_session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_answer = Column(Text, nullable=True)           # submitted text or JSON string for MCQs
    confidence = Column(Numeric(4, 2), nullable=True)  # 0.00–10.00
    correctness_score = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    evaluated_at = Column(TIMESTAMP(timezone=True), nullable=True)


class EvaluationResult(Base):
    """
    Multi-dimensional evaluation result per attempt. Used for both objective
    (MCQ/DOUBLE_MCQ) and subjective (AI) evaluation; subjective fills all fields.
    """
    __tablename__ = "evaluation_results"

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("question_attempts.id", ondelete="CASCADE"), primary_key=True)
    correctness = Column(Numeric(4, 3), nullable=False)           # 0.0–1.0
    conceptual_depth = Column(Numeric(4, 3), nullable=True)       # 0.0–1.0, mainly subjective
    reasoning_quality = Column(Numeric(4, 3), nullable=True)      # 0.0–1.0, mainly subjective
    confidence_alignment = Column(Numeric(4, 3), nullable=True)     # 0.0–1.0
    misconceptions = Column(JSON, nullable=True)        # list of strings
    feedback = Column(Text, nullable=True)
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


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class CourseUser(Base):
    __tablename__ = "course_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class CourseModule(Base):
    __tablename__ = "course_modules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_content_id = Column(UUID(as_uuid=True), ForeignKey("module_content.id", ondelete="CASCADE"), nullable=False)
    module_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
