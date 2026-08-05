import io
import hashlib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import models
from auth import get_current_user, check_permission, get_db
import difflib

router = APIRouter(prefix="/api/organization-imports", tags=["organization-imports"])

# Column mappings helper
COL_MAPPINGS = {
    "period": ["donem", "dönem", "period", "monthofyear", "month_of_year"],
    "hotel_code": ["otel_kodu", "otelkodu", "otel kodu", "otel", "hotel_code", "hotelcode"],
    "hotel_name": ["otel_adi", "oteladi", "otel adı", "otel adi", "hotel_name", "hotelname"],
    "city": ["sehir", "şehir", "city"],
    "region": ["bolge", "bölge", "region"],
    "main_category": ["anakategori", "ana kategori", "ana_kategori", "department", "departman"],
    "sub_main_category": ["altanakategori", "alt ana kategori", "alt_ana_kategori", "otel_alt"],
    "sub_category": ["altkategori", "alt kategori", "alt_kategori", "sub_department", "alt_departman"],
    "position_code": ["pozisyonkodu", "pozisyon kodu", "pozisyon_kodu", "position_code", "job_code"],
    "position_name": ["pozisyonadi", "pozisyon adı", "pozisyon_adi", "tanım", "tanım (pozisyon/isim/grade)", "position_name", "position"],
    "budget_fte": ["butcefte", "bütçefte", "bütçe fte", "bütçe", "bütce fte", "toplam fte", "toplam_fte", "budget_fte", "budget"],
    "active_fte": ["aktiffte", "aktif fte", "aktif_fte", "active_fte", "active"]
}

def find_mapped_col(columns: List[str], key: str) -> Optional[str]:
    for col in columns:
        if col in COL_MAPPINGS[key]:
            return col
    return None

class MappingRequest(BaseModel):
    excel_hotel_code: str
    system_hotel_id: int

@router.post("/upload")
async def upload_organization_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))
):
    try:
        contents = await file.read()
        file_hash = hashlib.md5(contents).hexdigest()
        
        # Check idempotency
        existing_import = db.query(models.OrganizationImport).filter(
            models.OrganizationImport.file_hash == file_hash
        ).first()
        
        # Read Excel sheet
        xls = pd.ExcelFile(io.BytesIO(contents))
        sheet_name = "Organizasyon_Butce_FTE"
        if sheet_name not in xls.sheet_names:
            sheet_name = xls.sheet_names[0]
            
        df = pd.read_excel(xls, sheet_name=sheet_name)
        orig_columns = list(df.columns)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Find column mappings
        col_map = {}
        for key in COL_MAPPINGS.keys():
            mapped = find_mapped_col(df.columns, key)
            if mapped:
                col_map[key] = orig_columns[df.columns.get_loc(mapped)]
            else:
                col_map[key] = None
                
        # Required validation
        required_keys = ["period", "hotel_code", "position_name", "budget_fte"]
        missing = [k for k in required_keys if col_map[k] is None]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Excel şablonunda zorunlu sütunlar eksik: {', '.join(missing)}. Mevcut sütunlar: {orig_columns}"
            )
            
        # Create import session record
        import_session = models.OrganizationImport(
            filename=file.filename,
            file_hash=file_hash,
            status="validating"
        )
        db.add(import_session)
        db.flush()
        
        total_rows = 0
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        
        preview_rows = []
        unmapped_hotel_codes = set()
        seen_keys = set()
        
        # Load system hotels for mapping & fuzzy matching
        system_hotels = db.query(models.Hotel).all()
        hotel_options = {h.code.lower(): h for h in system_hotels}
        hotel_names = {h.name.lower(): h for h in system_hotels}
        
        # Active mappings
        saved_mappings = {
            m.excel_hotel_code.lower(): m.system_hotel_id 
            for m in db.query(models.OrganizationImportMapping).all()
        }
        
        for idx, row in df.iterrows():
            total_rows += 1
            
            period_val = str(row.get(col_map["period"])).strip() if col_map["period"] else "2026-08"
            hotel_code_val = str(row.get(col_map["hotel_code"])).strip() if col_map["hotel_code"] else ""
            hotel_name_val = str(row.get(col_map["hotel_name"])).strip() if col_map["hotel_name"] else hotel_code_val
            city_val = str(row.get(col_map["city"])).strip() if col_map["city"] and not pd.isna(row.get(col_map["city"])) else "Antalya"
            region_val = str(row.get(col_map["region"])).strip() if col_map["region"] and not pd.isna(row.get(col_map["region"])) else "Kemer"
            main_category_val = str(row.get(col_map["main_category"])).strip() if col_map["main_category"] else "Genel"
            sub_main_val = str(row.get(col_map["sub_main_category"])).strip() if col_map["sub_main_category"] and not pd.isna(row.get(col_map["sub_main_category"])) else ""
            sub_cat_val = str(row.get(col_map["sub_category"])).strip() if col_map["sub_category"] and not pd.isna(row.get(col_map["sub_category"])) else ""
            pos_code_val = str(row.get(col_map["position_code"])).strip() if col_map["position_code"] and not pd.isna(row.get(col_map["position_code"])) else ""
            pos_name_val = str(row.get(col_map["position_name"])).strip() if col_map["position_name"] else ""
            
            # Safe parsing values
            try:
                b_fte = float(row.get(col_map["budget_fte"], 0.0))
                if pd.isna(b_fte):
                    b_fte = 0.0
            except Exception:
                b_fte = 0.0
                
            try:
                a_fte = float(row.get(col_map["active_fte"], 0.0)) if col_map["active_fte"] else 0.0
                if pd.isna(a_fte):
                    a_fte = 0.0
            except Exception:
                a_fte = 0.0

            # Default position code from name if missing
            if not pos_code_val:
                pos_code_val = pos_name_val.upper().replace(" ", "_")
                
            row_status = "valid"
            msg = None
            
            # Validate Period format (YYYY-MM or similar)
            if len(period_val) < 4:
                row_status = "invalid"
                msg = "Dönem formatı geçersiz (örneğin 2026-08 olmalı)."
            elif b_fte < 0 or a_fte < 0:
                row_status = "invalid"
                msg = "FTE değerleri negatif olamaz."
                
            # Duplicate check (same period, hotel, position)
            dup_key = f"{period_val}_{hotel_code_val}_{pos_code_val}"
            if dup_key in seen_keys:
                row_status = "warning"
                msg = "Aynı dönem, otel ve pozisyon için mükerrer kayıt."
            seen_keys.add(dup_key)
            
            # Check mapping status for this hotel code
            hotel_mapped = False
            if hotel_code_val.lower() in hotel_options or hotel_code_val.lower() in saved_mappings:
                hotel_mapped = True
            elif hotel_name_val.lower() in hotel_names:
                hotel_mapped = True
                
            if not hotel_mapped and hotel_code_val:
                unmapped_hotel_codes.add(hotel_code_val)
                
            # Create import row
            import_row = models.OrganizationImportRow(
                import_id=import_session.id,
                row_index=idx,
                period=period_val,
                hotel_code=hotel_code_val,
                hotel_name=hotel_name_val,
                city=city_val,
                region=region_val,
                main_category=main_category_val,
                sub_main_category=sub_main_val,
                sub_category=sub_cat_val,
                position_code=pos_code_val,
                position_name=pos_name_val,
                budget_fte=b_fte,
                active_fte=a_fte,
                status=row_status,
                validation_message=msg
            )
            db.add(import_row)
            
            if row_status == "valid":
                valid_count += 1
            elif row_status == "invalid":
                invalid_count += 1
            elif row_status == "warning":
                warning_count += 1
                
            if idx < 50:
                preview_rows.append({
                    "row_index": idx + 2,
                    "period": period_val,
                    "hotel_code": hotel_code_val,
                    "hotel_name": hotel_name_val,
                    "main_category": main_category_val,
                    "position_name": pos_name_val,
                    "budget_fte": b_fte,
                    "active_fte": a_fte,
                    "status": row_status,
                    "validation_message": msg
                })
                
        # Fuzzy suggestions for unmapped hotels
        unmapped_hotels_data = []
        for code in unmapped_hotel_codes:
            # Fuzzy match in existing hotels
            hotel_names_list = [h.name for h in system_hotels]
            matches = difflib.get_close_matches(code, hotel_names_list, n=3, cutoff=0.3)
            suggestions = []
            for m in matches:
                h = next((h for h in system_hotels if h.name == m), None)
                if h:
                    suggestions.append({"id": h.id, "name": h.name, "code": h.code})
            unmapped_hotels_data.append({
                "excel_code": code,
                "suggestions": suggestions
            })
            
        import_session.status = "ready_for_confirmation" if invalid_count == 0 else "validation_failed"
        db.commit()
        
        return {
            "import_id": import_session.id,
            "status": import_session.status,
            "filename": file.filename,
            "total_rows": total_rows,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "warning_count": warning_count,
            "unmapped_hotels": unmapped_hotels_data,
            "preview_rows": preview_rows,
            "already_uploaded": existing_import is not None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"İçe aktarma hatası: {str(e)}")

@router.post("/mappings")
def save_alias_mapping(
    req: MappingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))
):
    mapping = db.query(models.OrganizationImportMapping).filter(
        models.OrganizationImportMapping.excel_hotel_code == req.excel_hotel_code
    ).first()
    if not mapping:
        mapping = models.OrganizationImportMapping(
            excel_hotel_code=req.excel_hotel_code,
            system_hotel_id=req.system_hotel_id
        )
        db.add(mapping)
    else:
        mapping.system_hotel_id = req.system_hotel_id
    db.commit()
    return {"status": "success", "message": "Alias eşleme kaydedildi."}

@router.post("/confirm/{import_id}")
def confirm_import(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))
):
    import_session = db.query(models.OrganizationImport).get(import_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="İçe aktarma oturumu bulunamadı.")
        
    rows = db.query(models.OrganizationImportRow).filter(
        models.OrganizationImportRow.import_id == import_id
    ).all()
    
    # Load system hotels and mapping table
    system_hotels = db.query(models.Hotel).all()
    hotel_by_code = {h.code.lower(): h for h in system_hotels}
    hotel_by_name = {h.name.lower(): h for h in system_hotels}
    
    saved_mappings = {
        m.excel_hotel_code.lower(): m.system_hotel_id 
        for m in db.query(models.OrganizationImportMapping).all()
    }
    
    # Let's clear previous workforce lines to rebuild idempotently
    db.query(models.WorkforcePlanLine).delete()
    db.commit()
    
    imported_count = 0
    for r in rows:
        if r.status == "invalid":
            continue
            
        # Determine hotel entity
        hotel = None
        # 1. Excel code direct match
        if r.hotel_code.lower() in hotel_by_code:
            hotel = hotel_by_code[r.hotel_code.lower()]
        # 2. Saved mapping alias lookup
        elif r.hotel_code.lower() in saved_mappings:
            hotel_id = saved_mappings[r.hotel_code.lower()]
            hotel = db.query(models.Hotel).get(hotel_id)
        # 3. Name match
        elif r.hotel_name.lower() in hotel_by_name:
            hotel = hotel_by_name[r.hotel_name.lower()]
            
        # 4. Fallback: Dynamically create the hotel
        if not hotel:
            hotel = models.Hotel(
                name=r.hotel_name if r.hotel_name else r.hotel_code,
                code=r.hotel_code.upper().replace(" ", "_"),
                organization_id=1,
                city_id=1,
                region_id=1,
                branding_settings={"primary_color": "#0B4A3A", "logo_url": ""}
            )
            db.add(hotel)
            db.flush()
            # Cache it
            hotel_by_code[hotel.code.lower()] = hotel
            
        # Create canonical organization nodes closure dynamically
        # Level 1: Company (Root)
        company_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "company"
        ).first()
        if not company_node:
            company_node = models.OrganizationNode(
                name="Fine Otel Grubu",
                code="FINE_GROUP",
                level="company"
            )
            db.add(company_node)
            db.flush()
            company_node.path = str(company_node.id)
            db.flush()
            
        # Level 2: City
        city_name = r.city if r.city else "Antalya"
        city_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "city",
            models.OrganizationNode.name == city_name,
            models.OrganizationNode.parent_id == company_node.id
        ).first()
        if not city_node:
            city_node = models.OrganizationNode(
                name=city_name,
                code=city_name.upper().replace(" ", "_"),
                level="city",
                parent_id=company_node.id
            )
            db.add(city_node)
            db.flush()
            city_node.path = f"{company_node.path}/{city_node.id}"
            db.flush()
            
        # Level 3: Region
        region_name = r.region if r.region else "Kemer"
        region_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "region",
            models.OrganizationNode.name == region_name,
            models.OrganizationNode.parent_id == city_node.id
        ).first()
        if not region_node:
            region_node = models.OrganizationNode(
                name=region_name,
                code=region_name.upper().replace(" ", "_"),
                level="region",
                parent_id=city_node.id
            )
            db.add(region_node)
            db.flush()
            region_node.path = f"{city_node.path}/{region_node.id}"
            db.flush()
            
        # Level 4: Hotel
        hotel_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "hotel",
            models.OrganizationNode.code == hotel.code,
            models.OrganizationNode.parent_id == region_node.id
        ).first()
        if not hotel_node:
            hotel_node = models.OrganizationNode(
                name=hotel.name,
                code=hotel.code,
                level="hotel",
                parent_id=region_node.id
            )
            db.add(hotel_node)
            db.flush()
            hotel_node.path = f"{region_node.path}/{hotel_node.id}"
            db.flush()
            
        # Level 5: Main Category (Ana Kategori)
        main_cat_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "main_category",
            models.OrganizationNode.name == r.main_category,
            models.OrganizationNode.parent_id == hotel_node.id
        ).first()
        if not main_cat_node:
            main_cat_node = models.OrganizationNode(
                name=r.main_category,
                code=r.main_category.upper().replace(" ", "_"),
                level="main_category",
                parent_id=hotel_node.id
            )
            db.add(main_cat_node)
            db.flush()
            main_cat_node.path = f"{hotel_node.path}/{main_cat_node.id}"
            db.flush()
            
        # Level 6: Sub Main Category (Alt Ana Kategori)
        parent_node = main_cat_node
        if r.sub_main_category:
            sub_main_node = db.query(models.OrganizationNode).filter(
                models.OrganizationNode.level == "sub_main_category",
                models.OrganizationNode.name == r.sub_main_category,
                models.OrganizationNode.parent_id == main_cat_node.id
            ).first()
            if not sub_main_node:
                sub_main_node = models.OrganizationNode(
                    name=r.sub_main_category,
                    code=r.sub_main_category.upper().replace(" ", "_"),
                    level="sub_main_category",
                    parent_id=main_cat_node.id
                )
                db.add(sub_main_node)
                db.flush()
                sub_main_node.path = f"{main_cat_node.path}/{sub_main_node.id}"
                db.flush()
            parent_node = sub_main_node
            
        # Level 7: Sub Category (Alt Kategori)
        if r.sub_category:
            sub_cat_node = db.query(models.OrganizationNode).filter(
                models.OrganizationNode.level == "sub_category",
                models.OrganizationNode.name == r.sub_category,
                models.OrganizationNode.parent_id == parent_node.id
            ).first()
            if not sub_cat_node:
                sub_cat_node = models.OrganizationNode(
                    name=r.sub_category,
                    code=r.sub_category.upper().replace(" ", "_"),
                    level="sub_category",
                    parent_id=parent_node.id
                )
                db.add(sub_cat_node)
                db.flush()
                sub_cat_node.path = f"{parent_node.path}/{sub_cat_node.id}"
                db.flush()
            parent_node = sub_cat_node
            
        # Level 8: Position (Pozisyon)
        pos_node = db.query(models.OrganizationNode).filter(
            models.OrganizationNode.level == "position",
            models.OrganizationNode.code == r.position_code,
            models.OrganizationNode.parent_id == parent_node.id
        ).first()
        if not pos_node:
            pos_node = models.OrganizationNode(
                name=r.position_name,
                code=r.position_code,
                level="position",
                parent_id=parent_node.id
            )
            db.add(pos_node)
            db.flush()
            pos_node.path = f"{parent_node.path}/{pos_node.id}"
            db.flush()
            
        # Period
        period = db.query(models.WorkforcePlanPeriod).filter(
            models.WorkforcePlanPeriod.period_code == r.period
        ).first()
        if not period:
            period = models.WorkforcePlanPeriod(
                period_code=r.period
            )
            db.add(period)
            db.flush()
            
        # Workforce Plan Line
        plan_line = models.WorkforcePlanLine(
            period_id=period.id,
            node_id=pos_node.id,
            budget_fte=r.budget_fte,
            active_fte=r.active_fte
        )
        db.add(plan_line)
        
        # Keep old headcount and budget tables sync-ed!
        # Create department if not exists in legacy tables
        dept = db.query(models.Department).filter(
            (func.lower(models.Department.name) == func.lower(r.main_category)) |
            (func.lower(models.Department.code) == func.lower(r.main_category))
        ).first()
        if not dept:
            dept = models.Department(
                name=r.main_category,
                code=r.main_category.upper().replace(" ", "_")
            )
            db.add(dept)
            db.flush()
            
        legacy_budget = models.WorkforceHeadcountBudget(
            hotel_id=hotel.id,
            department_id=dept.id,
            position_title=r.position_name,
            headcount_budget=int(r.budget_fte),
            currency='TRY'
        )
        db.add(legacy_budget)
        
        # Clear specific workforce budget record index
        month_num = 8
        if len(r.period) >= 7:
            try:
                month_num = int(r.period.split("-")[1])
            except Exception:
                month_num = 8
                
        legacy_record = models.WorkforceBudgetRecord(
            tenant_id=1,
            hotel_code=hotel.code,
            hotel_sub=r.sub_main_category,
            department=r.main_category,
            sub_department=r.sub_category,
            position_title=r.position_name,
            month_of_year=month_num,
            total_fte=r.active_fte,
            budget_amount=r.budget_fte
        )
        db.add(legacy_record)
        
        imported_count += 1
        
    import_session.status = "completed"
    db.commit()
    
    return {
        "status": "success",
        "message": f"{imported_count} bütçe satırı ve organizasyon hiyerarşisi başarıyla içe aktarıldı.",
        "imported_count": imported_count
    }
