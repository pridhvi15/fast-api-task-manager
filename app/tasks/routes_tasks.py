from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Task, User
from app.schemas import TaskCreate, TaskUpdate
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/tasks", tags=["Tasks"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


#Admin-only: Create task
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create tasks")

    assigned_user = db.query(User).filter(User.id == task.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")

    if assigned_user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign tasks to another admin")

    new_task = Task(
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        priority=task.priority,
        created_by=current_user.id,
        acceptance_status="Pending",  # Default
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"msg": "Task created successfully", "task": new_task}


#Admin & Non-admin: List tasks
@router.get("/", status_code=status.HTTP_200_OK)
def list_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_admin:
        # Admin sees all tasks they created (accepted, rejected, pending)
        tasks = db.query(Task).filter(Task.created_by == current_user.id).all()
    else:
        # Non-admin sees only accepted tasks assigned to them by admins
        tasks = (
            db.query(Task)
            .join(User, Task.created_by == User.id)
            .filter(
                Task.assigned_to == current_user.id,
                User.is_admin == True,
                Task.acceptance_status == "Accepted"
            )
            .all()
        )
    return tasks


#Non-admin: View pending tasks (awaiting decision)
@router.get("/pending", status_code=status.HTTP_200_OK)
def list_pending_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins don't have pending tasks")
    pending_tasks = (
        db.query(Task)
        .join(User, Task.created_by == User.id)
        .filter(
            Task.assigned_to == current_user.id,
            User.is_admin == True,
            Task.acceptance_status == "Pending"
        )
        .all()
    )
    return pending_tasks


#Non-admin: Accept a task
@router.put("/accept/{task_id}", status_code=status.HTTP_200_OK)
def accept_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot accept tasks")

    if task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to accept this task")

    if task.acceptance_status == "Accepted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task already accepted")

    task.acceptance_status = "Accepted"
    db.commit()
    db.refresh(task)
    return {"msg": f"Task '{task.title}' accepted successfully", "task": task}


#Non-admin: Reject a task
@router.put("/reject/{task_id}", status_code=status.HTTP_200_OK)
def reject_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot reject tasks")

    if task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reject this task")

    if task.acceptance_status == "Rejected":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task already rejected")

    task.acceptance_status = "Rejected"
    db.commit()
    db.refresh(task)
    return {"msg": f"Task '{task.title}' rejected successfully", "task": task}


# Update task (status, details)
@router.put("/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: int, update: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not current_user.is_admin and task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")

    if current_user.is_admin:
        if update.title is not None: task.title = update.title
        if update.description is not None: task.description = update.description
        if update.priority is not None: task.priority = update.priority
        if update.status is not None: task.status = update.status
        if update.assigned_to is not None: task.assigned_to = update.assigned_to
    else:
        if update.status: task.status = update.status
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can only update task status")

    db.commit()
    db.refresh(task)
    return {"msg": "Task updated successfully", "task": task}


# Admin-only: Delete task
@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete tasks")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"msg": f"Task '{task.title}' deleted successfully"}
