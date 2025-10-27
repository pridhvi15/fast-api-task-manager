from pydantic import BaseModel
from typing import Optional
from typing import Optional, Literal

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    username: str
    password: str

class TaskBase(BaseModel):
    title: str
    description: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: int
    priority: Optional[Literal["High", "Medium", "Low"]] = "Medium"

class TaskUpdate(BaseModel):
    status: str

class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        orm_mode = True