from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.RecruitmentPipelineOut])
def list_pipelines(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.is_active == True).all()

@router.post("/", response_model=schemas.RecruitmentPipelineOut)
def create_pipeline(data: schemas.RecruitmentPipelineCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Check if a template with this name already exists
    existing = db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu isimde bir şablon zaten mevcut.")
    
    pipe = models.RecruitmentPipeline(**data.dict())
    db.add(pipe)
    db.commit()
    db.refresh(pipe)
    return pipe

@router.put("/{id}", response_model=schemas.RecruitmentPipelineOut)
def update_pipeline(id: int, data: schemas.RecruitmentPipelineCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    pipe = db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.id == id).first()
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline şablonu bulunamadı.")
    
    # Check if name is being taken by another template
    if data.name != pipe.name:
        existing = db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu isimde başka bir şablon mevcut.")
            
    pipe.name = data.name
    pipe.stages = data.stages
    pipe.is_active = data.is_active
    db.commit()
    db.refresh(pipe)
    return pipe

@router.delete("/{id}")
def delete_pipeline(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    pipe = db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.id == id).first()
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline şablonu bulunamadı.")
    db.delete(pipe)
    db.commit()
    return {"message": "Pipeline şablonu başarıyla silindi."}
