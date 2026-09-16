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
            # A candidate reaches a department through an application, the same way
            # it reaches a hotel. Joining Candidate straight to Position has no
            # path to follow, so this used to return nothing at all: a department
            # manager saw an empty talent pool while their board showed cards.
            allowed_depts = user.department_access_ids or []
            return query.filter(models.Candidate.id.in_(
                db.query(models.Application.candidate_id)
                  .join(models.Position, models.Application.position_id == models.Position.id)
                  .filter(models.Position.department_id.in_(allowed_depts))
            ))
            
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

    # ── Tekil kayıt erişimi ────────────────────────────────────────────────
    # The list endpoints filter by scope, but reading one record by id did not,
    # so an id in the URL walked straight past the hotel wall. These reuse the
    # same filters as the lists rather than restating the policy.

    @staticmethod
    def candidate_in_scope(db: Session, user: models.User, candidate_id: int):
        q = db.query(models.Candidate).filter(models.Candidate.id == candidate_id)
        return ScopePolicyService.apply_candidate_scope(q, db, user).first()

    @staticmethod
    def position_in_scope(db: Session, user: models.User, position_id: int):
        q = db.query(models.Position).filter(models.Position.id == position_id)
        return ScopePolicyService.apply_position_scope(q, db, user).first()

    @staticmethod
    def application_in_scope(db: Session, user: models.User, application_id: int):
        app = db.query(models.Application).filter(models.Application.id == application_id).first()
        if not app:
            return None
        if user.role in ("SYSTEM_ADMIN", "ADMIN") or user.data_visibility_scope == "GLOBAL":
            return app
        # An application belongs to whichever hotel its position belongs to.
        if app.position_id and ScopePolicyService.position_in_scope(db, user, app.position_id):
            return app
        return None


scope_policy_service = ScopePolicyService()
