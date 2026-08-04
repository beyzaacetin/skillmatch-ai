from sqlalchemy.orm import Session, Query
import models

class ScopePolicyService:
    @staticmethod
    def apply_candidate_scope(query: Query, db: Session, user: models.User) -> Query:
        # System admin / Admin always gets GLOBAL access
        if user.role in ("SYSTEM_ADMIN", "ADMIN") or user.data_visibility_scope == "GLOBAL":
            return query
            
        scope = (user.data_visibility_scope or "HOTEL").upper()
        
        if scope == "REGIONAL":
            # Filter candidates associated with positions in allowed regions
            allowed_regions = user.region_access_ids or []
            # Find hotels in these regions
            hotel_ids = [h.id for h in db.query(models.Hotel).filter(models.Hotel.region_id.in_(allowed_regions)).all()]
            return query.join(models.Position, isouter=True).filter(
                (models.Position.hotel_id.in_(hotel_ids)) | 
                (models.Candidate.id.in_(
                    db.query(models.Application.candidate_id).filter(models.Application.hotel_id.in_(hotel_ids))
                ))
            )
            
        elif scope == "HOTEL":
            allowed_hotels = user.hotel_access_ids or []
            return query.join(models.Position, isouter=True).filter(
                (models.Position.hotel_id.in_(allowed_hotels)) |
                (models.Candidate.id.in_(
                    db.query(models.Application.candidate_id).filter(models.Application.hotel_id.in_(allowed_hotels))
                ))
            )
            
        elif scope == "DEPARTMENT":
            allowed_depts = user.department_access_ids or []
            return query.join(models.Position, isouter=True).filter(
                models.Position.department_id.in_(allowed_depts)
            )
            
        elif scope == "OWN_RECORDS":
            return query.filter(models.Candidate.deleted_by == user.full_name)
            
        return query

    @staticmethod
    def apply_position_scope(query: Query, db: Session, user: models.User) -> Query:
        if user.role in ("SYSTEM_ADMIN", "ADMIN") or user.data_visibility_scope == "GLOBAL":
            return query
            
        scope = (user.data_visibility_scope or "HOTEL").upper()
        
        if scope == "REGIONAL":
            allowed_regions = user.region_access_ids or []
            hotel_ids = [h.id for h in db.query(models.Hotel).filter(models.Hotel.region_id.in_(allowed_regions)).all()]
            return query.filter(models.Position.hotel_id.in_(hotel_ids))
            
        elif scope == "HOTEL":
            allowed_hotels = user.hotel_access_ids or []
            return query.filter(models.Position.hotel_id.in_(allowed_hotels))
            
        elif scope == "DEPARTMENT":
            allowed_depts = user.department_access_ids or []
            return query.filter(models.Position.department_id.in_(allowed_depts))
            
        return query

scope_policy_service = ScopePolicyService()
