from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
import models
import database
import auth
import schemas
from auth import get_current_user, check_permission, get_db

router = APIRouter()

def log_audit(db: Session, user: models.User, action: str, target_type: str, target_id: Optional[int], details: dict, request: Optional[Request] = None):
    from config import settings
    if not settings.ENABLE_AUDIT_LOGGING:
        return
    ip_addr = request.client.host if request and request.client else None
    from services.audit_service import audit_service
    audit_service.log(db, user, action, target_type, target_id, details, ip_addr)

# ─── PYDANTIC SCHEMAS ────────────────────────────────────────────────────────

class OrganizationSchema(BaseModel):
    name: str
    code: str
    is_active: Optional[bool] = True
    order_index: Optional[int] = 0

class HotelSchema(BaseModel):
    organization_id: int
    city_id: int
    region_id: int
    name: str
    code: str
    branding_settings: Optional[dict] = {}
    is_active: Optional[bool] = True

class DepartmentSchema(BaseModel):
    name: str
    code: str
    is_active: Optional[bool] = True
    order_index: Optional[int] = 0

class MappingSchema(BaseModel):
    hotel_id: int
    department_id: int
    position_title: str

class RoleSchema(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    permissions: dict
    is_custom: Optional[bool] = True

class ConfigUpdateSchema(BaseModel):
    value: Any
    hotel_id: Optional[int] = None

# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

# ─── Organization Hierarchy Endpoints ───

@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Organization).order_by(models.Organization.order_index).all()

@router.post("/organizations")
def create_organization(data: OrganizationSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    existing = db.query(models.Organization).filter(models.Organization.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kodlu bir organizasyon zaten var.")
    org = models.Organization(**data.dict())
    db.add(org)
    db.commit()
    db.refresh(org)
    log_audit(db, current_user, "create", "organization", org.id, data.dict(), request)
    return org

@router.put("/organizations/{id}")
def update_organization(id: int, data: OrganizationSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    org = db.query(models.Organization).filter(models.Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organizasyon bulunamadı")
    org.name = data.name
    org.code = data.code
    org.is_active = data.is_active
    org.order_index = data.order_index
    db.commit()
    log_audit(db, current_user, "update", "organization", org.id, data.dict(), request)
    return org

@router.get("/countries")
def list_countries(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Country).all()

@router.get("/cities")
def list_cities(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.City).all()

@router.get("/regions")
def list_regions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Region).all()

@router.get("/hotels")
def list_hotels(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Scope based listing: If not GLOBAL scope, filter hotels
    if current_user.role == "SYSTEM_ADMIN" or current_user.role == "ADMIN" or current_user.data_visibility_scope == "GLOBAL":
        return db.query(models.Hotel).all()
    
    # Otherwise check user's access list
    allowed_ids = current_user.hotel_access_ids or []
    return db.query(models.Hotel).filter(models.Hotel.id.in_(allowed_ids)).all()

@router.post("/hotels")
def create_hotel(data: HotelSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    existing = db.query(models.Hotel).filter(models.Hotel.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kodlu bir otel zaten var.")
    hotel = models.Hotel(**data.dict())
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    log_audit(db, current_user, "create", "hotel", hotel.id, data.dict(), request)
    return hotel

@router.put("/hotels/{id}")
def update_hotel(id: int, data: HotelSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Otel bulunamadı")
    hotel.name = data.name
    hotel.code = data.code
    hotel.organization_id = data.organization_id
    hotel.city_id = data.city_id
    hotel.region_id = data.region_id
    hotel.branding_settings = data.branding_settings
    hotel.is_active = data.is_active
    db.commit()
    log_audit(db, current_user, "update", "hotel", hotel.id, data.dict(), request)
    return hotel

@router.get("/departments")
def list_departments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Department).order_by(models.Department.order_index).all()

@router.post("/departments")
def create_department(data: DepartmentSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    existing = db.query(models.Department).filter(models.Department.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kodlu bir departman zaten var.")
    dept = models.Department(**data.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_audit(db, current_user, "create", "department", dept.id, data.dict(), request)
    return dept

@router.put("/departments/{id}")
def update_department(id: int, data: DepartmentSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    dept = db.query(models.Department).filter(models.Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departman bulunamadı")
    dept.name = data.name
    dept.code = data.code
    dept.is_active = data.is_active
    dept.order_index = data.order_index
    db.commit()
    log_audit(db, current_user, "update", "department", dept.id, data.dict(), request)
    return dept

# ─── Mapping Endpoints ───

@router.get("/mappings")
def list_mappings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.HotelDepartmentPositionMapping).all()

@router.post("/mappings")
def create_mapping(data: MappingSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    exists = db.query(models.HotelDepartmentPositionMapping).filter(
        models.HotelDepartmentPositionMapping.hotel_id == data.hotel_id,
        models.HotelDepartmentPositionMapping.department_id == data.department_id,
        models.HotelDepartmentPositionMapping.position_title == data.position_title
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bu eşleşme zaten tanımlanmış.")
    mapping = models.HotelDepartmentPositionMapping(**data.dict())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    log_audit(db, current_user, "create", "mapping", mapping.id, data.dict(), request)
    return mapping

@router.delete("/mappings/{id}")
def delete_mapping(id: int, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    mapping = db.query(models.HotelDepartmentPositionMapping).filter(models.HotelDepartmentPositionMapping.id == id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Eşleşme bulunamadı")
    db.delete(mapping)
    db.commit()
    log_audit(db, current_user, "delete", "mapping", id, {"id": id}, request)
    return {"message": "Eşleşme silindi."}

# ─── Dynamic Roles & Permissions Endpoints ───

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Role).all()

@router.post("/roles")
def create_role(data: RoleSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    existing = db.query(models.Role).filter(models.Role.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kodlu bir rol zaten var.")
    role = models.Role(**data.dict())
    db.add(role)
    db.commit()
    db.refresh(role)
    log_audit(db, current_user, "create", "role", role.id, data.dict(), request)
    return role

@router.put("/roles/{id}")
def update_role(id: int, data: RoleSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    role = db.query(models.Role).filter(models.Role.id == id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol bulunamadı")
    if not role.is_custom:
        raise HTTPException(status_code=400, detail="Sistem rollerini değiştiremezsiniz, sadece özel rolleri güncelleyebilirsiniz.")
    role.name = data.name
    role.description = data.description
    role.permissions = data.permissions
    db.commit()
    log_audit(db, current_user, "update", "role", role.id, data.dict(), request)
    return role

# ─── System Configurations Endpoints ───

@router.get("/configs")
def list_configs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.SystemConfiguration).all()

@router.put("/configs/{key}")
def update_config(key: str, data: ConfigUpdateSchema, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    cfg = db.query(models.SystemConfiguration).filter(
        models.SystemConfiguration.key == key,
        models.SystemConfiguration.hotel_id == data.hotel_id
    ).first()
    if not cfg:
        # Create hotel specific configuration override
        cfg = models.SystemConfiguration(
            key=key,
            value=data.value,
            hotel_id=data.hotel_id,
            category="custom"
        )
        db.add(cfg)
    else:
        cfg.value = data.value
    db.commit()
    log_audit(db, current_user, "update_config", "config", cfg.id, {"key": key, "value": data.value, "hotel_id": data.hotel_id}, request)
    return cfg

# ─── Audit Log Endpoints ───

@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db), current_user: models.User = Depends(check_permission("can_access_settings"))):
    return db.query(models.ImmutableAuditLog).order_by(models.ImmutableAuditLog.created_at.desc()).limit(200).all()


# ─── WORKFORCE HEADCOUNT BUDGET & SCOPED ROUTING ENDPOINTS (Phase 3) ─────────

from fastapi import UploadFile, File, Body
import pandas as pd
import io
from datetime import datetime, timezone, timedelta

@router.post("/headcount-budget/import")
def import_headcount_budget(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))
):
    """Imports workforce headcount budget from Excel file."""
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_mappings = {
            "hotel": ["hotel name", "hotel", "otel", "otel adı"],
            "department": ["department", "departman", "bölüm"],
            "position": ["position", "position title", "pozisyon", "unvan"],
            "budget": ["headcount budget", "budget", "bütçe", "kontenjan", "headcount"],
            "salary_min": ["target salary min", "salary min", "min maaş", "minimum maaş", "salary_min"],
            "salary_max": ["target salary max", "salary max", "max maaş", "maksimum maaş", "salary_max"],
            "currency": ["currency", "para birimi", "döviz"]
        }
        
        def find_col(key):
            for col in df.columns:
                if col in col_mappings[key]:
                    return col
            return None

        hotel_col = find_col("hotel")
        dept_col = find_col("department")
        pos_col = find_col("position")
        budget_col = find_col("budget")
        salary_min_col = find_col("salary_min")
        salary_max_col = find_col("salary_max")
        curr_col = find_col("currency")

        if not hotel_col or not dept_col or not pos_col or not budget_col:
            raise HTTPException(
                status_code=400,
                detail=f"Excel dosyası gerekli sütunları içermelidir: Otel, Departman, Pozisyon, Bütçe. Mevcut: {list(df.columns)}"
            )

        db.query(models.WorkforceHeadcountBudget).delete()
        db.commit()

        imported_count = 0
        skipped_rows = []

        for idx, row in df.iterrows():
            hotel_val = str(row[hotel_col]).strip()
            dept_val = str(row[dept_col]).strip()
            pos_val = str(row[pos_col]).strip()
            budget_val = row[budget_col]

            if pd.isna(hotel_val) or pd.isna(dept_val) or pd.isna(pos_val) or pd.isna(budget_val):
                continue

            try:
                hotel = db.query(models.Hotel).filter(func.lower(models.Hotel.name) == func.lower(hotel_val)).first()
                if not hotel:
                    skipped_rows.append(f"Satır {idx+2}: Otel '{hotel_val}' sistemde bulunamadı.")
                    continue

                dept = db.query(models.Department).filter(func.lower(models.Department.name) == func.lower(dept_val)).first()
                if not dept:
                    skipped_rows.append(f"Satır {idx+2}: Departman '{dept_val}' sistemde bulunamadı.")
                    continue

                budget_num = int(budget_val)
                sal_min = int(row[salary_min_col]) if salary_min_col and not pd.isna(row[salary_min_col]) else None
                sal_max = int(row[salary_max_col]) if salary_max_col and not pd.isna(row[salary_max_col]) else None
                curr = str(row[curr_col]).strip() if curr_col and not pd.isna(row[curr_col]) else 'TRY'

                budget = models.WorkforceHeadcountBudget(
                    hotel_id=hotel.id,
                    department_id=dept.id,
                    position_title=pos_val,
                    headcount_budget=budget_num,
                    target_salary_min=sal_min,
                    target_salary_max=sal_max,
                    currency=curr
                )
                db.add(budget)
                imported_count += 1
            except Exception as row_err:
                skipped_rows.append(f"Satır {idx+2}: Hata - {str(row_err)}")

        db.commit()
        
        log_audit(
            db=db,
            user=current_user,
            action="import_headcount_budget",
            target_type="headcount_budget",
            target_id=None,
            details={"imported_rows": imported_count, "errors": skipped_rows}
        )

        return {
            "message": f"Bütçe tablosu başarıyla içe aktarıldı. Toplam {imported_count} kayıt eklendi.",
            "skipped": skipped_rows
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Tablo içe aktarılırken hata oluştu: {str(e)}")


@router.get("/headcount-budget")
def list_headcount_budgets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Fetch all headcount budgets, formatted with Hotel & Department Names."""
    budgets = db.query(models.WorkforceHeadcountBudget).all()
    res = []
    for b in budgets:
        hotel = db.query(models.Hotel).filter_by(id=b.hotel_id).first()
        dept = db.query(models.Department).filter_by(id=b.department_id).first()
        res.append({
            "id": b.id,
            "hotel_id": b.hotel_id,
            "hotel_name": hotel.name if hotel else "Bilinmeyen Otel",
            "department_id": b.department_id,
            "department_name": dept.name if dept else "Bilinmeyen Departman",
            "position_title": b.position_title,
            "headcount_budget": b.headcount_budget,
            "target_salary_min": b.target_salary_min,
            "target_salary_max": b.target_salary_max,
            "currency": b.currency
        })
    return res


@router.get("/routing-suggestions")
def list_routing_suggestions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Retrieve candidate suggestions routed due to headcount budget exhaustion."""
    q = db.query(models.CandidateRoutingSuggestion)
    if current_user.role not in ["ADMIN", "SYSTEM_ADMIN", "CENTRAL_HR"]:
        allowed_hotels = current_user.hotel_access_ids or []
        q = q.filter(models.CandidateRoutingSuggestion.target_hotel_id.in_(allowed_hotels))
    
    suggestions = q.order_by(models.CandidateRoutingSuggestion.created_at.desc()).all()
    res = []
    for s in suggestions:
        cand = db.query(models.Candidate).filter_by(id=s.candidate_id).first()
        source = db.query(models.Hotel).filter_by(id=s.source_hotel_id).first()
        target = db.query(models.Hotel).filter_by(id=s.target_hotel_id).first()
        res.append({
            "id": s.id,
            "candidate_id": s.candidate_id,
            "candidate_name": cand.name if cand else "Bilinmeyen Aday",
            "source_hotel_id": s.source_hotel_id,
            "source_hotel_name": source.name if source else "Bilinmeyen Otel",
            "target_hotel_id": s.target_hotel_id,
            "target_hotel_name": target.name if target else "Bilinmeyen Otel",
            "position_title": s.position_title,
            "status": s.status,
            "created_at": s.created_at
        })
    return res


@router.put("/routing-suggestions/{id}/resolve")
def resolve_routing_suggestion(
    id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Accept or reject candidate suggestion routed from sister hotel."""
    suggestion = db.query(models.CandidateRoutingSuggestion).filter_by(id=id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Yönlendirme önerisi bulunamadı")

    if status not in ["ACCEPTED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Geçersiz durum değeri.")

    suggestion.status = status
    db.commit()

    if status == "ACCEPTED":
        position = db.query(models.Position).filter(
            models.Position.hotel_id == suggestion.target_hotel_id,
            func.lower(models.Position.title) == func.lower(suggestion.position_title),
            models.Position.is_active == True
        ).first()

        if not position:
            position = db.query(models.Position).filter(
                models.Position.hotel_id == suggestion.target_hotel_id,
                models.Position.is_active == True
            ).first()

        if position:
            now_utc = datetime.now(timezone.utc)
            source_hotel = db.query(models.Hotel).filter_by(id=suggestion.source_hotel_id).first()
            source_name = source_hotel.name if source_hotel else "Kardeş Otel"
            app = models.Application(
                candidate_id=suggestion.candidate_id,
                position_id=position.id,
                status="applied",
                status_history=[{"status": "applied", "date": now_utc.isoformat(), "note": f"{source_name} yönlendirmesi kabul edildi."}],
                source="Routed Suggestion",
                hotel_id=suggestion.target_hotel_id,
                ownership_started_at=now_utc,
                ownership_expires_at=now_utc + timedelta(days=10),
                lock_status='LOCKED'
            )
            db.add(app)
            db.commit()

    return {"message": "Öneri durumu başarıyla güncellendi.", "status": status}


# ─── SALARY POLICY ENDPOINTS (Phase 4) ───────────────────────────────────────

@router.post("/salary-policy/import")
def import_salary_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))
):
    """Imports salary policy bands from Excel file."""
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_mappings = {
            "hotel": ["hotel name", "hotel", "otel", "otel adı"],
            "department": ["department", "departman", "bölüm"],
            "position": ["position", "position title", "pozisyon", "unvan", "tanim (pozisyon/isim/grade)"],
            "seniority": ["seniority", "seniority level", "seviye", "derece", "grade"],
            "min_salary": ["min salary", "min maaş", "minimum maaş", "salary min", "min_salary"],
            "target_salary": ["target salary", "hedef maaş", "hedef ücret", "target_salary"],
            "max_salary": ["max salary", "max maaş", "maksimum maaş", "salary max", "max_salary"],
            "accommodation": ["accommodation", "lojman"],
            "transportation": ["transportation", "servis", "ulaşım"],
            "meal": ["meal", "yemek"],
            "bonus": ["bonus", "prim"],
            "currency": ["currency", "para birimi", "döviz"]
        }
        
        def find_col(key):
            for col in df.columns:
                if col in col_mappings[key]:
                    return col
            return None

        hotel_col = find_col("hotel")
        dept_col = find_col("department")
        pos_col = find_col("position")
        seniority_col = find_col("seniority")
        min_sal_col = find_col("min_salary")
        target_sal_col = find_col("target_salary")
        max_sal_col = find_col("max_salary")
        accommodation_col = find_col("accommodation")
        trans_col = find_col("transportation")
        meal_col = find_col("meal")
        bonus_col = find_col("bonus")
        curr_col = find_col("currency")

        if not pos_col or not min_sal_col or not max_sal_col or not target_sal_col:
            raise HTTPException(
                status_code=400,
                detail=f"Excel dosyası gerekli sütunları içermelidir: Pozisyon, Min Maaş, Hedef Maaş, Max Maaş. Mevcut: {list(df.columns)}"
            )

        db.query(models.SalaryPolicy).delete()
        db.commit()

        imported_count = 0
        skipped_rows = []

        for idx, row in df.iterrows():
            pos_val = str(row[pos_col]).strip()
            min_val = row[min_sal_col]
            target_val = row[target_sal_col]
            max_val = row[max_sal_col]

            if pd.isna(pos_val) or pd.isna(min_val) or pd.isna(target_val) or pd.isna(max_val):
                continue

            hotel_val = str(row[hotel_col]).strip() if hotel_col and not pd.isna(row[hotel_col]) else None
            dept_val = str(row[dept_col]).strip() if dept_col and not pd.isna(row[dept_col]) else None
            seniority_val = str(row[seniority_col]).strip() if seniority_col and not pd.isna(row[seniority_col]) else None
            
            acc_val = str(row[accommodation_col]).strip().lower() in ['yes', 'true', '1', 'evet', 'y'] if accommodation_col and not pd.isna(row[accommodation_col]) else False
            trans_val = str(row[trans_col]).strip().lower() in ['yes', 'true', '1', 'evet', 'y'] if trans_col and not pd.isna(row[trans_col]) else False
            meal_val = str(row[meal_col]).strip().lower() in ['yes', 'true', '1', 'evet', 'y'] if meal_col and not pd.isna(row[meal_col]) else False
            bonus_val = str(row[bonus_col]).strip() if bonus_col and not pd.isna(row[bonus_col]) else None
            curr = str(row[curr_col]).strip() if curr_col and not pd.isna(row[curr_col]) else 'TRY'

            try:
                hotel_id = None
                if hotel_val:
                    hotel = db.query(models.Hotel).filter(func.lower(models.Hotel.name) == func.lower(hotel_val)).first()
                    if not hotel:
                        # Try matching code
                        hotel = db.query(models.Hotel).filter(func.lower(models.Hotel.code) == func.lower(hotel_val)).first()
                    if hotel:
                        hotel_id = hotel.id

                dept_id = None
                if dept_val:
                    dept = db.query(models.Department).filter(func.lower(models.Department.name) == func.lower(dept_val)).first()
                    if dept:
                        dept_id = dept.id

                policy = models.SalaryPolicy(
                    hotel_id=hotel_id,
                    department_id=dept_id,
                    position_title=pos_val,
                    seniority_level=seniority_val,
                    min_salary=int(min_val),
                    target_salary=int(target_val),
                    max_salary=int(max_val),
                    accommodation=acc_val,
                    transportation=trans_val,
                    meal=meal_val,
                    bonus=bonus_val,
                    currency=curr
                )
                db.add(policy)
                imported_count += 1
            except Exception as row_err:
                skipped_rows.append(f"Satır {idx+2}: Hata - {str(row_err)}")

        db.commit()
        
        log_audit(
            db=db,
            user=current_user,
            action="import_salary_policy",
            target_type="salary_policy",
            target_id=None,
            details={"imported_rows": imported_count, "errors": skipped_rows}
        )

        return {
            "message": f"Maaş politikası tablosu başarıyla içe aktarıldı. Toplam {imported_count} kayıt eklendi.",
            "skipped": skipped_rows
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Maaş tablosu içe aktarılırken hata oluştu: {str(e)}")


@router.get("/salary-policy", response_model=List[schemas.SalaryPolicyOut])
def list_salary_policies(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Fetch all salary policies."""
    return db.query(models.SalaryPolicy).all()

