# IntelliGrade System Architecture & Logic Flow

This document provides a comprehensive overview of the IntelliGrade backend system, its components, and how they interact. It is designed to help developers and AI agents understand the codebase quickly.

---

## 🏗 Project Structure

The project follows a modular "Engine-based" architecture:

- `core/`: Shared infrastructure (Security, GenAI service).
- `entities/`: Database layer (SQLAlchemy models, Alembic migrations).
- `engines/`: Self-contained business logic modules.
- `main.py`: Entry point that assembles all engines into a single FastAPI app.

---

## 🧩 Core Engines & Logic

### 1. **Auth & User Management** (`engines/auth`, `engines/user_management`)
- **Purpose**: Handles JWT-based authentication and user profiles.
- **Logic**: Uses `bcrypt` for hashing and `python-jose` for tokens.
- **Inter-relation**: Most protected routes use `get_current_user_id` as a dependency.

### 2. **Quiz Engine** (`engines/quiz_engine`)
- **Purpose**: Manages the lifecycle of a student quiz.
- **Key Logic**:
    - **Start**: Resumes an existing incomplete session for a (User, Module) or selects 10 new questions based on a 40/30/30 distribution (MCQ, Double MCQ, Subjective).
    - **Submit**: Evaluates objective answers deterministically and subjective answers via Gemini AI.
    - **Result**: Aggregates scores across dimensions (Correctness, Depth, Reasoning, Confidence Alignment).
- **Inter-relation**: 
    - Calls **Evaluation Engine** after every submission to sync scores centrally.
    - Uses **Core/GenAI** for subjective scoring.

### 3. **Evaluation Engine** (`engines/evaluation_engine`)
- **Purpose**: A centralized service for rigorous AI-based evaluation of any student input.
- **Key Logic**: Uses extremely strict Gemini prompting to score answers on a 0-1 scale.
- **Inter-relation**: 
    - Called by **Quiz Engine** and potentially other modules.
    - Calls **Score Engine** to persist the result in the global `scores` table.

### 4. **Score Engine** (`engines/score_engine`)
- **Purpose**: The "Single Source of Truth" for user performance data.
- **Key Logic**:
    - **Creation**: Stores weighted scores from various sources (`evaluation_engine`, `conversation_engine`, etc.).
    - **Aggregation**: Calculates a **Total Module Score** using a weighted formula: `0.5 (Completion) + 0.35 (Evaluation) + 0.15 (Conversation)`.
    - **Color Grading**: Assigns a status color based on total score:
        - `0.00 - 0.25`: Yellow
        - `0.25 - 0.50`: Blue
        - `0.50 - 0.75`: Orange
        - `0.75 - 1.00`: Red
- **Inter-relation**: Collects data from all other engines.

### 5. **Conversation Engine** (`engines/conversation_engine`)
- **Purpose**: Real-time AI tutor that explains module content to students.
- **Key Logic**: Uses Gemini 1.5 Pro with a "10-year-old difficulty" persona. It evaluates the user's follow-up questions to update their understanding score.
- **Inter-relation**: Syncs results to **Score Engine**.

### 6. **Progress & Completion** (`engines/progress`)
- **Purpose**: Tracks module status.
- **Key Logic**: Allows users to mark modules as "Complete" which unlocks the quiz.
- **Inter-relation**: 
    - Dependencies in **Quiz Engine** prevent starting a quiz unless the module is marked complete.
    - Provides a "Module Understanding" endpoint that pulls data from the latest **Quiz Engine** result.

---

## 🔄 Data Flow Example: Submitting a Quiz Answer

1.  **Frontend** sends answer to `POST /quiz/submit`.
2.  **Quiz Engine**:
    - Validates the attempt.
    - Creates a `QuestionAttempt` record.
    - Runs local evaluation (deterministic or AI).
    - Updates the `QuizSession` (marks complete if last question).
3.  **Cross-Engine Sync** (Internal):
    - Quiz Engine calls `Evaluation Engine` service.
    - Evaluation Engine performs a strict AI check.
    - Evaluation Engine calls `Score Engine` to save a permanent score record.
4.  **Database**: Both local `evaluation_results` and global `scores` tables are updated.

---

## 🛠 Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Migrations**: Alembic
- **AI**: Google Gemini (google-genai)
- **Security**: JWT (OAuth2 Password Bearer)
- **Validation**: Pydantic v2

---

## 🔑 Key Database Tables
- `users`: Core user data.
- `module_content`: The educational text/material.
- `questions`: The question bank.
- `quiz_sessions` & `question_attempts`: Quiz state.
- `scores`: Centralized performance records.
- `user_module_completion`: Progress tracking.
