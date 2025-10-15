from fastapi import FastAPI
from app.database import Base, engine
from app.auth import routes_auth
from app.users.routes_user import router as user_router
from app.tasks import routes_tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API with JWT")

app.include_router(routes_auth.router)
app.include_router(user_router)
app.include_router(routes_tasks.router)
