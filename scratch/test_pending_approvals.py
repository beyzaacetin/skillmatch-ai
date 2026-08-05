import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
import models

try:
    engine = create_engine("sqlite:///backend/skillmatch.db")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Try querying pending approvals
    query = db.query(models.OfferApprovalRequest).join(models.Offer).join(models.Application).filter(
        models.OfferApprovalRequest.status == "PENDING"
    )
    
    # Just run the query and options
    results = query.options(
        joinedload(models.OfferApprovalRequest.offer).joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).all()
    
    print(f"Success! Found {len(results)} pending approvals.")
except Exception as e:
    print("Error querying pending approvals:")
    traceback.print_exc()
