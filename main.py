from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from engines.auth import router as auth_router
from engines.user_management import router as user_management_router
from engines.conversation_engine import router as conversation_engine_router
from engines.question_engine import router as question_engine_router
from engines.evaluation_engine import router as evaluation_engine_router
from engines.score_engine import router as score_engine_router
from engines.content_loading import router as content_loading_router
from engines.quiz_engine import router as quiz_router
from engines.progress import router as progress_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(user_management_router.router)
app.include_router(conversation_engine_router.router)
app.include_router(question_engine_router.router)
app.include_router(evaluation_engine_router.router)
app.include_router(score_engine_router.router)
app.include_router(content_loading_router.router)
app.include_router(quiz_router.router)
app.include_router(progress_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to IntelliGrade API"}
