import logging
from sqlalchemy.orm import Session
import models
import datetime

logger = logging.getLogger(__name__)

def validate_offer_salary(hotel_id: int, department_id: int, position_title: str, proposed_salary: int, db: Session) -> dict:
    """
    Validates the proposed offer salary against the active SalaryPolicy.
    Looks for a specific hotel/department match first, falling back to a position title match.
    """
    if not proposed_salary:
        return {"has_policy": False, "is_valid": True}

    # Query matching policy
    policy = db.query(models.SalaryPolicy).filter(
        models.SalaryPolicy.hotel_id == hotel_id,
        models.SalaryPolicy.department_id == department_id,
        models.SalaryPolicy.position_title.collate("NOCASE") == position_title.strip(),
        models.SalaryPolicy.is_active == True
    ).first()

    # Fallback to hotel-level default for the position title if department not matched
    if not policy:
        policy = db.query(models.SalaryPolicy).filter(
            models.SalaryPolicy.hotel_id == hotel_id,
            models.SalaryPolicy.position_title.collate("NOCASE") == position_title.strip(),
            models.SalaryPolicy.is_active == True
        ).first()

    # Generic fallback
    if not policy:
        policy = db.query(models.SalaryPolicy).filter(
            models.SalaryPolicy.position_title.collate("NOCASE") == position_title.strip(),
            models.SalaryPolicy.is_active == True
        ).first()

    if not policy:
        return {
            "has_policy": False,
            "is_valid": True,
            "min_salary": None,
            "target_salary": None,
            "max_salary": None,
            "currency": "TRY",
            "deviation_amount": 0,
            "deviation_percent": 0
        }

    is_valid = policy.min_salary <= proposed_salary <= policy.max_salary
    deviation_amount = proposed_salary - policy.target_salary
    deviation_percent = round((deviation_amount / policy.target_salary) * 100, 2) if policy.target_salary else 0

    return {
        "has_policy": True,
        "is_valid": is_valid,
        "min_salary": policy.min_salary,
        "target_salary": policy.target_salary,
        "max_salary": policy.max_salary,
        "currency": policy.currency,
        "accommodation": policy.accommodation,
        "transportation": policy.transportation,
        "meal": policy.meal,
        "bonus": policy.bonus,
        "additional_benefits": policy.additional_benefits,
        "deviation_amount": deviation_amount,
        "deviation_percent": deviation_percent
    }


def create_offer_approval_flow(offer_id: int, db: Session):
    """
    Creates sequential OfferApprovalRequests for an offer that requires exception approval:
      1. HOTEL_HR (Sequence 1) - PENDING
      2. CENTRAL_HR (Sequence 2) - WAITING
    """
    # Delete any existing pending/waiting approval requests for this offer
    db.query(models.OfferApprovalRequest).filter_by(offer_id=offer_id).delete()
    db.commit()

    # Step 1: Hotel HR Approval (represented by HOTEL_HR role)
    req1 = models.OfferApprovalRequest(
        offer_id=offer_id,
        approver_role="HOTEL_HR",
        sequence_number=1,
        status="PENDING"
    )
    # Step 2: Central HR Approval (represented by CENTRAL_HR or SYSTEM_ADMIN)
    req2 = models.OfferApprovalRequest(
        offer_id=offer_id,
        approver_role="CENTRAL_HR",
        sequence_number=2,
        status="WAITING"
    )
    db.add(req1)
    db.add(req2)
    db.commit()
    logger.info(f"Created sequential approval requests for Offer ID {offer_id}")
