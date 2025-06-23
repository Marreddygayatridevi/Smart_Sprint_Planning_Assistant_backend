from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth
from src.database.db import create_tables
from src.utils.config import settings
from src.api.routes import team
from src.api.routes import jira
from src.api.routes import sprints
from src.api.routes import ai  


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    create_tables()

app.include_router(auth.router)
app.include_router(team.router)
app.include_router(jira.router)
app.include_router(sprints.router)
app.include_router(ai.router) 


