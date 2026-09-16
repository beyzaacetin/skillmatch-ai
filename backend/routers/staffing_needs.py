from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import models, schemas, auth, database
from datetime import datetime, date

router = APIRouter()

@router.get("/", response_model=List[schemas.StaffingNeedOut])
def get_staffing_needs(
    hotel_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    q = db.query(models.StaffingNeed)

    # The list took current_user but never used it: every hotel's and every
    # department's requests were visible to everyone who could open the page.
    scope = (current_user.data_visibility_scope or "").upper()
    if current_user.role not in ("ADMIN", "SYSTEM_ADMIN") and scope != "GLOBAL":
        if scope == "DEPARTMENT":
            q = q.filter(models.StaffingNeed.department_id.in_(current_user.department_access_ids or []))
        elif current_user.hotel_access_ids:
            q = q.filter(models.StaffingNeed.hotel_id.in_(current_user.hotel_access_ids))

    if hotel_id:
        q = q.filter(models.StaffingNeed.hotel_id == hotel_id)
    if department_id:
        q = q.filter(models.StaffingNeed.department_id == department_id)
    if status:
        q = q.filter(func.lower(models.StaffingNeed.status) == status.lower())
    if priority:
        q = q.filter(func.lower(models.StaffingNeed.priority) == priority.lower())
    return q.order_by(models.StaffingNeed.created_at.desc()).all()

@router.post("/", response_model=dict)
def create_manual_staffing_need(
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not payload.get("hotel_id"):
        raise HTTPException(status_code=400, detail="Otel seçilmelidir.")
    if not payload.get("position_title"):
        raise HTTPException(status_code=400, detail="Pozisyon başlığı zorunludur.")

    needed_by = payload.get("needed_by")
    if needed_by:
        try:
            needed_by = date.fromisoformat(needed_by)
        except ValueError:
            raise HTTPException(status_code=400, detail="İhtiyaç tarihi GG.AA.YYYY biçiminde okunamadı.")
    else:
        needed_by = None

    need = models.StaffingNeed(
        hotel_id=payload["hotel_id"],
        department_id=payload.get("department_id") or None,
        position_title=payload["position_title"],
        needed_fte=payload.get("needed_fte", 1.0),
        needed_by=needed_by,
        priority=payload.get("priority", "normal"),
        source="manual",
        notes=payload.get("notes")
    )
    db.add(need)
    db.commit()
    db.refresh(need)
    return {"id": need.id, "status": "created"}

@router.post("/auto-detect", response_model=dict)
def auto_detect_staffing_needs(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    gaps = db.query(models.WorkforcePlanLine).filter(models.WorkforcePlanLine.budget_fte > models.WorkforcePlanLine.active_fte).all()
    created_count = 0
    for gap in gaps:
        needed_fte = gap.budget_fte - gap.active_fte
        node = db.query(models.OrganizationNode).filter(models.OrganizationNode.id == gap.node_id).first()
        if not node: continue
        
        # We need to find hotel id from the node tree, assuming there's some linkage or we fall back to a default.
        # For simplicity, if we cannot find hotel_id, we just use 1.
        hotel_id = 1
        
        existing = db.query(models.StaffingNeed).filter(
            models.StaffingNeed.organization_node_id == gap.node_id,
            models.StaffingNeed.status == "pending"
        ).first()
        
        if not existing:
            need = models.StaffingNeed(
                hotel_id=hotel_id,
                organization_node_id=gap.node_id,
                position_title=node.name,
                needed_fte=needed_fte,
                source="budget_gap"
            )
            db.add(need)
            created_count += 1
    db.commit()
    return {"created_count": created_count}

CENTRAL_APPROVER_ROLES = ["ADMIN", "SYSTEM_ADMIN", "CENTRAL_HR"]


def require_central_approver(current_user: models.User):
    """A hotel raises the request; approving it opens a position and spends
    budget, so the decision belongs to merkez."""
    if current_user.role not in CENTRAL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Kadro talebini yalnızca merkez onaylayabilir")


@router.put("/{id}/approve", response_model=dict)
def approve_staffing_need(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    require_central_approver(current_user)
    need = db.query(models.StaffingNeed).filter(models.StaffingNeed.id == id).first()
    if not need: raise HTTPException(status_code=404, detail="Need not found")
    
    if need.status == "approved":
        return {"id": need.id, "status": need.status, "message": "Already approved"}
        
    need.status = "approved"
    need.approved_by_id = current_user.id
    need.approved_at = datetime.utcnow()
    
    pos = models.Position(
        hotel_id=need.hotel_id,
        department_id=need.department_id,
        title=need.position_title,
        headcount=need.needed_fte,   # 2,5 FTE 2 kadroya kırpılmasın
        is_active=True
    )
    db.add(pos)
    db.commit()
    db.refresh(pos)
    
    need.created_position_id = pos.id
    db.commit()
    
    return {"id": need.id, "status": "approved", "created_position_id": pos.id}

@router.put("/{id}/reject", response_model=dict)
def reject_staffing_need(
    id: int,
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    require_central_approver(current_user)
    need = db.query(models.StaffingNeed).filter(models.StaffingNeed.id == id).first()
    if not need: raise HTTPException(status_code=404, detail="Need not found")
    
    need.status = "rejected"
    need.rejection_reason = payload.get("reason", "No reason provided")
    db.commit()
    return {"id": need.id, "status": "rejected"}

@router.get("/summary", response_model=dict)
def staffing_needs_summary(
    hotel_id: Optional[int] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    q = db.query(models.StaffingNeed)
    if hotel_id:
        q = q.filter(models.StaffingNeed.hotel_id == hotel_id)
        
    all_needs = q.all()
    pending = sum(1 for n in all_needs if n.status == "pending")
    approved = sum(1 for n in all_needs if n.status == "approved")
    rejected = sum(1 for n in all_needs if n.status == "rejected")
    total_gap = sum(n.needed_fte or 0 for n in all_needs if n.status == "pending")

    return {
        "pending_count": pending,
        "approved_count": approved,
        "rejected_count": rejected,
        "total_gap_fte": round(total_gap, 2)
    }
