import models
from sqlalchemy.orm import Session
from datetime import datetime, timezone

def seed_multi_hotel_foundation(db: Session):
    try:
        # 1. Seed Roles
        roles_data = [
            {
                "name": "Sistem Yöneticisi",
                "code": "SYSTEM_ADMIN",
                "description": "Tüm sistem yetkilerine sahip üst kullanıcı.",
                "permissions": {
                    "can_access_settings": True,
                    "can_see_salaries": True,
                    "can_edit_salaries": True,
                    "can_approve_offers": True,
                    "can_manage_users": True,
                    "can_export_data": True,
                    "can_blacklist": True,
                    "can_view_reports": True
                },
                "is_custom": False
            },
            {
                "name": "Merkez İK",
                "code": "CENTRAL_HR",
                "description": "Tüm otelleri ve süreçleri görebilen, onay verebilen İK kullanıcısı.",
                "permissions": {
                    "can_access_settings": True,
                    "can_see_salaries": True,
                    "can_edit_salaries": True,
                    "can_approve_offers": True,
                    "can_manage_users": True,
                    "can_export_data": True,
                    "can_blacklist": True,
                    "can_view_reports": True
                },
                "is_custom": False
            },
            {
                "name": "Bölge İK",
                "code": "REGIONAL_HR",
                "description": "Sadece kendi bölgesindeki otelleri görebilen İK kullanıcısı.",
                "permissions": {
                    "can_access_settings": False,
                    "can_see_salaries": True,
                    "can_edit_salaries": False,
                    "can_approve_offers": True,
                    "can_manage_users": False,
                    "can_export_data": True,
                    "can_blacklist": True,
                    "can_view_reports": True
                },
                "is_custom": False
            },
            {
                "name": "Otel İK",
                "code": "HOTEL_HR",
                "description": "Sadece kendi otelindeki süreçleri yöneten İK kullanıcısı.",
                "permissions": {
                    "can_access_settings": False,
                    "can_see_salaries": True,
                    "can_edit_salaries": False,
                    "can_approve_offers": False,
                    "can_manage_users": False,
                    "can_export_data": False,
                    "can_blacklist": True,
                    "can_view_reports": True
                },
                "is_custom": False
            },
            {
                "name": "Departman Yöneticisi",
                "code": "DEPARTMENT_MANAGER",
                "description": "Sadece kendi otel ve departmanındaki adayları değerlendiren yönetici.",
                "permissions": {
                    "can_access_settings": False,
                    "can_see_salaries": False,
                    "can_edit_salaries": False,
                    "can_approve_offers": False,
                    "can_manage_users": False,
                    "can_export_data": False,
                    "can_blacklist": False,
                    "can_view_reports": False
                },
                "is_custom": False
            }
        ]
        
        db_roles = {}
        for r_dict in roles_data:
            role = db.query(models.Role).filter(models.Role.code == r_dict["code"]).first()
            if not role:
                role = models.Role(**r_dict)
                db.add(role)
                db.flush()
            else:
                role.permissions = r_dict["permissions"]
                db.add(role)
            db_roles[r_dict["code"]] = role

        # 2. Seed Organization
        org = db.query(models.Organization).filter(models.Organization.code == "RIXOS_TR").first()
        if not org:
            org = models.Organization(name="Rixos Türkiye", code="RIXOS_TR", order_index=0)
            db.add(org)
            db.flush()

        # 3. Seed Country
        country = db.query(models.Country).filter(models.Country.code == "TR").first()
        if not country:
            country = models.Country(name="Türkiye", code="TR")
            db.add(country)
            db.flush()

        # 4. Seed City
        city = db.query(models.City).filter(models.City.name == "Antalya").first()
        if not city:
            city = models.City(name="Antalya", country_id=country.id)
            db.add(city)
            db.flush()

        # 5. Seed Region
        region = db.query(models.Region).filter(models.Region.name == "Kemer").first()
        if not region:
            region = models.Region(name="Kemer", city_id=city.id)
            db.add(region)
            db.flush()

        # 6. Seed Hotels
        hotels_data = [
            {"name": "Rixos Sungate", "code": "RIXOS_SUNGATE"},
            {"name": "Rixos Tekirova", "code": "RIXOS_TEKIROVA"},
            {"name": "Rixos Beldibi", "code": "RIXOS_BELDIBI"}
        ]
        db_hotels = {}
        for h_dict in hotels_data:
            hotel = db.query(models.Hotel).filter(models.Hotel.code == h_dict["code"]).first()
            if not hotel:
                hotel = models.Hotel(
                    name=h_dict["name"],
                    code=h_dict["code"],
                    organization_id=org.id,
                    city_id=city.id,
                    region_id=region.id,
                    branding_settings={"primary_color": "#0B4A3A", "logo_url": ""}
                )
                db.add(hotel)
                db.flush()
            db_hotels[h_dict["code"]] = hotel

        # 7. Seed Departments
        depts_data = [
            {"name": "Yiyecek ve İçecek", "code": "F_B"},
            {"name": "Kat Hizmetleri", "code": "HOUSEKEEPING"},
            {"name": "Mutfak", "code": "KITCHEN"},
            {"name": "Ön Büro", "code": "FRONT_OFFICE"},
            {"name": "İnsan Kaynakları", "code": "HR"}
        ]
        db_depts = {}
        for d_dict in depts_data:
            dept = db.query(models.Department).filter(models.Department.code == d_dict["code"]).first()
            if not dept:
                dept = models.Department(name=d_dict["name"], code=d_dict["code"])
                db.add(dept)
                db.flush()
            db_depts[d_dict["code"]] = dept

        # 8. Seed Hotel-Department-Position Mapping templates
        mappings_data = [
            {"hotel_code": "RIXOS_SUNGATE", "dept_code": "F_B", "pos_title": "Garson"},
            {"hotel_code": "RIXOS_SUNGATE", "dept_code": "HOUSEKEEPING", "pos_title": "Kat Hizmetleri Görevlisi"},
            {"hotel_code": "RIXOS_SUNGATE", "dept_code": "HR", "pos_title": "İK Uzmanı"},
            {"hotel_code": "RIXOS_TEKIROVA", "dept_code": "F_B", "pos_title": "Garson"},
            {"hotel_code": "RIXOS_TEKIROVA", "dept_code": "HOUSEKEEPING", "pos_title": "Kat Hizmetleri Görevlisi"},
            {"hotel_code": "RIXOS_BELDIBI", "dept_code": "F_B", "pos_title": "Garson"}
        ]
        for m in mappings_data:
            h_obj = db_hotels.get(m["hotel_code"])
            d_obj = db_depts.get(m["dept_code"])
            if h_obj and d_obj:
                exists = db.query(models.HotelDepartmentPositionMapping).filter(
                    models.HotelDepartmentPositionMapping.hotel_id == h_obj.id,
                    models.HotelDepartmentPositionMapping.department_id == d_obj.id,
                    models.HotelDepartmentPositionMapping.position_title == m["pos_title"]
                ).first()
                if not exists:
                    mapping = models.HotelDepartmentPositionMapping(
                        hotel_id=h_obj.id,
                        department_id=d_obj.id,
                        position_title=m["pos_title"]
                    )
                    db.add(mapping)

        # 9. Seed System Configurations
        configs = [
            {
                "key": "ownership_duration_days",
                "value": 10,
                "category": "ownership",
                "description": "İlk aday sahiplenme süresi (gün)"
            },
            {
                "key": "ownership_warning_day_1",
                "value": 7,
                "category": "ownership",
                "description": "İlk aday sahiplenme uyarı günü"
            },
            {
                "key": "ownership_warning_day_2",
                "value": 9,
                "category": "ownership",
                "description": "Kritik aday sahiplenme uyarı günü"
            },
            {
                "key": "ownership_critical_day",
                "value": 10,
                "category": "ownership",
                "description": "Ortak havuza transfer günü"
            },
            {
                "key": "timer_reset_actions",
                "value": ["interview_scheduled", "phone_call_logged", "interview_completed", "offer_created", "status_changed"],
                "category": "ownership",
                "description": "Sahiplenme süresini sıfırlayan İK işlemleri"
            },
            {
                "key": "duplicate_fields",
                "value": ["phone", "email"],
                "category": "duplicates",
                "description": "Aday mükerrerlik tespit alanları"
            },
            {
                "key": "simultaneous_applications_allowed",
                "value": False,
                "category": "locks",
                "description": "Adayın birden fazla otelde aktif sürecinin olabilmesi"
            }
        ]
        for c_dict in configs:
            cfg = db.query(models.SystemConfiguration).filter(
                models.SystemConfiguration.key == c_dict["key"],
                models.SystemConfiguration.hotel_id == None
            ).first()
            if not cfg:
                cfg = models.SystemConfiguration(
                    key=c_dict["key"],
                    value=c_dict["value"],
                    category=c_dict["category"],
                    description=c_dict["description"]
                )
                db.add(cfg)

        # 10. Update demo user to SYSTEM_ADMIN and map access
        demo_user = db.query(models.User).filter(models.User.email == "demo@skillmatch.ai").first()
        if demo_user:
            admin_role = db_roles.get("SYSTEM_ADMIN")
            if admin_role:
                demo_user.role_id = admin_role.id
                demo_user.role = "SYSTEM_ADMIN"
            sungate = db_hotels.get("RIXOS_SUNGATE")
            if sungate:
                demo_user.hotel_access_ids = [sungate.id]
            demo_user.data_visibility_scope = "GLOBAL"
            db.add(demo_user)

        # 11. Retroactive backfill for existing users, positions, and applications
        default_hotel = db_hotels.get("RIXOS_SUNGATE")
        default_dept = db_depts.get("HR")
        default_role = db_roles.get("HOTEL_HR")
        
        if default_hotel:
            # Positions
            positions = db.query(models.Position).filter(models.Position.hotel_id == None).all()
            for p in positions:
                p.hotel_id = default_hotel.id
                if p.department:
                    dept_match = db.query(models.Department).filter(models.Department.name.like(f"%{p.department}%")).first()
                    if dept_match:
                        p.department_id = dept_match.id
                db.add(p)

            # Applications
            applications = db.query(models.Application).filter(models.Application.hotel_id == None).all()
            for a in applications:
                a.hotel_id = default_hotel.id
                db.add(a)

            # Users
            users = db.query(models.User).filter(models.User.role_id == None).all()
            for u in users:
                u.hotel_access_ids = [default_hotel.id]
                u.data_visibility_scope = "HOTEL"
                u_role_upper = u.role.upper() if u.role else ""
                if u_role_upper in ["ADMIN", "SYSTEM_ADMIN", "AGENCY_ADMIN", "SUPER_ADMIN"]:
                    u.role_id = db_roles.get("SYSTEM_ADMIN").id
                    u.data_visibility_scope = "GLOBAL"
                elif u_role_upper in ["RECRUITER", "HR", "AGENCY_RECRUITER", "HOTEL_HR", "CENTRAL_HR", "REGIONAL_HR"]:
                    u.role_id = default_role.id
                    u.data_visibility_scope = "HOTEL"
                elif u_role_upper in ["HIRING_MANAGER", "MANAGER", "DEPARTMENT_MANAGER"]:
                    u.role_id = db_roles.get("DEPARTMENT_MANAGER").id
                    u.data_visibility_scope = "DEPARTMENT"
                else:
                    # Fallback to HOTEL_HR
                    u.role_id = default_role.id
                    u.data_visibility_scope = "HOTEL"
                db.add(u)
                
        # Seed default recruitment pipeline templates
        pipeline_templates = [
            {
                "name": "Mavi Yaka Hızlı Akış",
                "stages": ["Yeni Başvuru", "Ön Değerlendirme", "İK Mülakatı", "Teknik Mülakat", "Teklif", "Belge Süreci", "İşe Giriş"]
            },
            {
                "name": "Standart İşe Alım Akışı",
                "stages": ["Yeni Başvuru", "Aday Tarama", "Mülakat", "Referans Kontrolü", "Teklif", "İşe Giriş"]
            },
            {
                "name": "Yönetici / Executive Süreci",
                "stages": ["Yeni Başvuru", "İK Ön Görüşme", "Panel Mülakatı", "Yönetim Değerlendirmesi", "Teklif", "İşe Giriş"]
            }
        ]
        for pt in pipeline_templates:
            exists = db.query(models.RecruitmentPipeline).filter(models.RecruitmentPipeline.name == pt["name"]).first()
            if not exists:
                new_pipe = models.RecruitmentPipeline(
                    name=pt["name"],
                    stages=pt["stages"]
                )
                db.add(new_pipe)

        db.commit()
        print("[Startup] Seeded multi-hotel hierarchy and recruitment pipelines successfully.")
    except Exception as e:
        db.rollback()
        print(f"[Startup] Seeding multi-hotel hierarchy failed: {e}")
        import traceback
        traceback.print_exc()
