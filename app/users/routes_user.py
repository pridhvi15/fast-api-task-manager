# users/routes_user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserOut
from app.auth.routes_auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserOut])
def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    
    users = db.query(User).all()
    return users
