from fastapi import FastAPI
from engines.user_management import router as user_management_router
from engines.conversation_engine import router as conversation_engine_router
from engines.question_engine import router as question_engine_router
from engines.evaluation_engine import router as evaluation_engine_router
from engines.score_engine import router as score_engine_router

app = FastAPI()

app.include_router(user_management_router.router)
app.include_router(conversation_engine_router.router)
app.include_router(question_engine_router.router)
app.include_router(evaluation_engine_router.router)
app.include_router(score_engine_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to IntelliGrade API"}
