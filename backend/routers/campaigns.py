from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import database
import models
import schemas
import auth
import os
import urllib.request
import urllib.parse

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

def generate_qr_code_helper(data: str, filename: str) -> str:
    try:
        encoded_data = urllib.parse.quote(data)
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}"
        upload_dir = "backend/static/qrcodes"
        os.makedirs(upload_dir, exist_ok=True)
        dest_path = os.path.join(upload_dir, filename)
        
        # Download and save the image
        urllib.request.urlretrieve(url, dest_path)
        return f"/static/qrcodes/{filename}"
    except Exception as e:
        print(f"QR Generation helper error: {e}")
        # Fallback placeholder
        return "/static/qrcodes/placeholder.png"

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
    # In production, we'd point to the deployed portal domain
    utm_url = f"https://skillmatch-os-prototype.susry.chatgpt.site/portal/apply/{campaign_in.position_id}{query_str}"
    
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
        utm_url = f"https://skillmatch-os-prototype.susry.chatgpt.site/portal/apply/{c.position_id}{query_str}"
        
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
