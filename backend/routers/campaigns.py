from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import database
import models
import schemas
import auth
from config import settings
import os
import urllib.parse

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

def generate_qr_code_helper(data: str, filename: str) -> str:
    try:
        import qrcode
        # Relative to the CWD this landed in backend/backend/static/qrcodes when the
        # app is started from backend/, i.e. outside the directory mounted at /static.
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "qrcodes")
        os.makedirs(upload_dir, exist_ok=True)
        dest_path = os.path.join(upload_dir, filename)

        # Drawn locally rather than fetched from api.qrserver.com: the campaign is
        # created in front of the candidate (or on stage), so it cannot depend on a
        # third-party service being reachable at that moment.
        img = qrcode.make(data, box_size=10, border=2)
        img.save(dest_path)
        return f"/static/qrcodes/{filename}"
    except Exception as e:
        # No placeholder.png ships with the repo, so returning one renders a broken
        # image; an empty path lets the UI show that there is no QR yet.
        print(f"QR Generation helper error: {e}")
        return ""

@router.post("/", response_model=schemas.RecruitmentCampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_in: schemas.RecruitmentCampaignCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify position exists
    position = db.query(models.Position).filter(models.Position.id == campaign_in.position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı")
        
    # Construct UTM URL pointing to public application page
    utm_params = []
    if campaign_in.utm_source:
        utm_params.append(f"utm_source={urllib.parse.quote(campaign_in.utm_source)}")
    if campaign_in.utm_medium:
        utm_params.append(f"utm_medium={urllib.parse.quote(campaign_in.utm_medium)}")
    if campaign_in.utm_campaign:
        utm_params.append(f"utm_campaign={urllib.parse.quote(campaign_in.utm_campaign)}")
        
    query_str = f"?{'&'.join(utm_params)}" if utm_params else ""
    # /portal/apply/... is not a route the SPA knows: it falls through to the
    # staff login screen, so a candidate scanning the QR saw a login form.
    utm_url = f"{settings.FRONTEND_URL.rstrip('/')}/portal/job/{campaign_in.position_id}{query_str}"
    
    # Save campaign db record
    db_campaign = models.RecruitmentCampaign(
        name=campaign_in.name,
        hotel_id=campaign_in.hotel_id,
        position_id=campaign_in.position_id,
        source=campaign_in.source or "QR Code",
        utm_source=campaign_in.utm_source,
        utm_medium=campaign_in.utm_medium,
        utm_campaign=campaign_in.utm_campaign,
        qr_code_path=""
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    # Generate QR Code image file
    qr_filename = f"campaign_{db_campaign.id}.png"
    qr_path = generate_qr_code_helper(utm_url, qr_filename)
    
    db_campaign.qr_code_path = qr_path
    db.commit()
    db.refresh(db_campaign)
    
    # Attach dynamic utm_url field for out schemas
    res = schemas.RecruitmentCampaignOut.model_validate(db_campaign)
    res.utm_url = utm_url
    return res

@router.get("/", response_model=List[schemas.RecruitmentCampaignOut])
def list_campaigns(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    campaigns = db.query(models.RecruitmentCampaign).all()
    results = []
    for c in campaigns:
        utm_params = []
        if c.utm_source:
            utm_params.append(f"utm_source={urllib.parse.quote(c.utm_source)}")
        if c.utm_medium:
            utm_params.append(f"utm_medium={urllib.parse.quote(c.utm_medium)}")
        if c.utm_campaign:
            utm_params.append(f"utm_campaign={urllib.parse.quote(c.utm_campaign)}")
        query_str = f"?{'&'.join(utm_params)}" if utm_params else ""
        utm_url = f"{settings.FRONTEND_URL.rstrip('/')}/portal/job/{c.position_id}{query_str}"
        
        out = schemas.RecruitmentCampaignOut.model_validate(c)
        out.utm_url = utm_url
        results.append(out)
    return results

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    c = db.query(models.RecruitmentCampaign).filter(models.RecruitmentCampaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")
    db.delete(c)
    db.commit()
    return None
