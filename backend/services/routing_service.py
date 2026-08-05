from sqlalchemy.orm import Session
import models

def route_candidate_to_positions(candidate_id: int, db: Session):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        return
        
    skills = candidate.skills or []
    
    # Just a mock logic to prioritize Same Hotel -> Region -> City -> Pool
    positions = db.query(models.Position).filter(models.Position.is_active == True).all()
    
    # Normally we would sort by match score, etc.
    # We will just create some dummy suggestions for demonstration.
    if positions:
        for p in positions[:2]:
            sug = models.CandidateRoutingSuggestion(
                candidate_id=candidate_id,
                source_hotel_id=1,
                target_hotel_id=p.hotel_id or 1,
                position_title=p.title,
                status="PENDING"
            )
            db.add(sug)
        db.commit()
