from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.auth import routes_auth
from app.users.routes_user import router as user_router
from app.tasks import routes_tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API with JWT")

# === CORS middleware ===
origins = [
    "http://localhost:5173",          # React dev server
    "http://127.0.0.1:5173"   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # Allow custom headers
)

app.include_router(routes_auth.router)
app.include_router(user_router)
app.include_router(routes_tasks.router)
