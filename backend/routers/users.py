from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database, auth
from auth import get_password_hash, require_roles
from datetime import datetime, timezone

router = APIRouter()

def _log_user_action(db: Session, admin: models.User, action: str, target_id: int, target_name: str, details: dict = {}):
    log_detail = {
        "admin_email": admin.email,
        "target_name": target_name,
        **details
    }
    log = models.Log(
        user_id=admin.id,
        user_name=admin.full_name,
        action=action,
        target_type="user",
        target_id=target_id,
        details=log_detail
    )
    db.add(log)
    db.commit()

@router.get("/", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin lists all users."""
    return db.query(models.User).all()

@router.post("/", response_model=schemas.UserOut, status_code=201)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin creates a new user."""
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta adresiyle kayıtlı bir kullanıcı zaten var.")
    
    new_user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        department=user_in.department,
        phone=user_in.phone,
        is_active=True,
        is_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    _log_user_action(db, current_user, "user_created", new_user.id, new_user.full_name, {
        "email": new_user.email,
        "role": new_user.role,
        "department": new_user.department
    })
    
    return new_user

@router.put("/{id}", response_model=schemas.UserOut)
def update_user(
    id: int,
    user_in: schemas.UserAdminUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin updates user details."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    old_role = user.role
    
    # Check if admin is trying to demote themselves
    if user.id == current_user.id and user_in.role and user_in.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail="Kendi admin yetkinizi düşüremezsiniz.")
        
    if user_in.full_name is not None: user.full_name = user_in.full_name
    if user_in.email is not None: user.email = user_in.email
    if user_in.department is not None: user.department = user_in.department
    if user_in.role is not None: user.role = user_in.role
    if user_in.is_active is not None: user.is_active = user_in.is_active
    if user_in.password is not None and user_in.password.strip() != "":
        user.hashed_password = get_password_hash(user_in.password)
        
    db.commit()
    db.refresh(user)
    
    _log_user_action(db, current_user, "user_updated", user.id, user.full_name, {
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active
    })
    
    return user

@router.put("/{id}/role", response_model=schemas.UserOut)
def update_user_role(
    id: int,
    data: schemas.UserRoleUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin changes user role."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    if user.id == current_user.id and data.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail="Kendi admin yetkinizi düşüremezsiniz.")
        
    old_role = user.role
    user.role = data.role
    db.commit()
    db.refresh(user)
    
    _log_user_action(db, current_user, "user_role_changed", user.id, user.full_name, {
        "old_role": old_role,
        "new_role": user.role
    })
    
    return user

@router.put("/{id}/reset-password")
def reset_password(
    id: int,
    data: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin resets a user's password."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    new_password = data.get("password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Geçersiz şifre (En az 6 karakter olmalıdır)")
        
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    _log_user_action(db, current_user, "user_password_reset", user.id, user.full_name)
    return {"message": f"{user.full_name} şifresi başarıyla yenilendi."}

@router.put("/{id}/deactivate", response_model=schemas.UserOut)
def deactivate_user(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin deactivates a user."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı pasifleştiremezsiniz.")
        
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    _log_user_action(db, current_user, "user_deactivated", user.id, user.full_name)
    return user

@router.put("/{id}/activate", response_model=schemas.UserOut)
def activate_user(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Admin activates a user."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    _log_user_action(db, current_user, "user_activated", user.id, user.full_name)
    return user

@router.delete("/{id}", response_model=schemas.UserOut)
def delete_user(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN))
):
    """Soft delete: deactivates user instead of hard deleting."""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz/pasifleştiremezsiniz.")
        
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    _log_user_action(db, current_user, "user_deactivated", user.id, user.full_name, {"note": "Soft deleted"})
    return user
