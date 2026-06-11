from sqlalchemy.orm import Session
import models
import json
from services.semantic_matcher import semantic_matcher

class MatcherService:
    def match_candidates(self, position_id: int, db: Session):
        position = db.query(models.Position).filter(models.Position.id == position_id).first()
        if not position:
            return []

        candidates = db.query(models.Candidate).filter(models.Candidate.is_deleted == False).all()
        matches = []

        from services.llm_matcher import llm_matcher_service

        for candidate in candidates:
            try:
                match_score = llm_matcher_service.match_candidate_position(candidate.id, position_id, db)
                matches.append({
                    "candidate": candidate,
                    "score": round(match_score.overall_score or 0.0, 1),
                    "matching_skills": match_score.matching_skills or [],
                    "semantic_score": round(match_score.culture_fit_score or 0.0, 1),
                    "keyword_score": round(match_score.required_skill_score or 0.0, 1),
                    "learning_boost": round(match_score.experience_score or 0.0, 1)
                })
            except Exception as e:
                print(f"[Matcher] LLM matching failed for candidate {candidate.id}: {e}")

        # Sort by score desc
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

matcher_service = MatcherService()
