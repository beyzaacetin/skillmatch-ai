from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, auth

router = APIRouter()

@router.get("/", response_model=List[schemas.RecruitmentTaskOut])
def get_tasks(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.RecruitmentTask).all()

@router.post("/", response_model=schemas.RecruitmentTaskOut, status_code=201)
def create_task(task_in: schemas.RecruitmentTaskCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = models.RecruitmentTask(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status or "todo",
        assigned_to=task_in.assigned_to,
        due_date=task_in.due_date
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{id}", response_model=schemas.RecruitmentTaskOut)
def update_task(id: int, task_in: schemas.RecruitmentTaskCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = db.query(models.RecruitmentTask).filter(models.RecruitmentTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    task.title = task_in.title
    task.description = task_in.description
    if task_in.status:
        task.status = task_in.status
    task.assigned_to = task_in.assigned_to
    task.due_date = task_in.due_date
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{id}", status_code=204)
def delete_task(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = db.query(models.RecruitmentTask).filter(models.RecruitmentTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    db.delete(task)
    db.commit()
    return None
