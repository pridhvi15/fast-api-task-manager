# users/routes_user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserOut
from app.auth.routes_auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserOut])
def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    
    users = db.query(User).all()
    return users

class UserBasicInfo(BaseModel):
    id: int
    username: str

@router.get("/non_admin_usernames", response_model=list[UserBasicInfo])
def get_non_admin_usernames(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    
    users = db.query(User.id, User.username).filter(User.is_admin == False).all()
    # SQLAlchemy returns list of tuples → convert to list of dicts
    return [{"id": u[0], "username": u[1]} for u in users]