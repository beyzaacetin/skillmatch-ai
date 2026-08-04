import sys
import os
import pandas as pd
import numpy as np

# Add backend folder to sys.path
sys.path.insert(0, r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend")

from database import SessionLocal
import models

def import_data():
    db = SessionLocal()
    try:
        print("--- Loading Excel Sheets ---")
        df_mappings = pd.read_excel(r"C:\Users\sule\Desktop\Otel_Departman_Pozisyon.xlsx")
        df_budgets = pd.read_excel(r"C:\Users\sule\Desktop\bütçemevcut.xlsx")
        
        def clean_cols(df):
            replacements = {
                'ı': 'i', 'İ': 'I',
                'ü': 'u', 'Ü': 'U',
                'ö': 'o', 'Ö': 'O',
                'ç': 'c', 'Ç': 'C',
                'ş': 's', 'Ş': 'S',
                'ğ': 'g', 'Ğ': 'G'
            }
            new_cols = []
            for col in df.columns:
                c_str = str(col).strip()
                for old, new in replacements.items():
                    c_str = c_str.replace(old, new)
                new_cols.append(c_str)
            df.columns = new_cols
            return df

        df_mappings = clean_cols(df_mappings)
        df_budgets = clean_cols(df_budgets)

        # Mapping for hotel codes to full names
        hotel_names_map = {
            'SUN': 'Rixos Sungate',
            'TKR': 'Rixos Tekirova',
            'BLD': 'Rixos Beldibi',
            'BDR': 'Rixos Bodrum',
            'PRM': 'Rixos Premium Belek',
            'DWT': 'Rixos Downtown Antalya',
            'PARK': 'The Land of Legends Theme Park',
            'THM': 'Rixos Theme Park',
            'PRBL': 'Rixos Premium Bodrum',
            'NICK': 'Club Privé By Rixos Gocek',
            'GCK': 'Rixos Premium Göcek',
            'PRA': 'Rixos Premium Almaty'
        }

        # 1. Resolve and import unique Hotels
        print("\n1. Importing Hotels...")
        unique_hotels = df_mappings['Otel'].dropna().unique()
        db_hotels = {}
        for code in unique_hotels:
            name = hotel_names_map.get(code, f"Rixos {code}")
            hotel = db.query(models.Hotel).filter_by(code=code).first()
            if not hotel:
                hotel = models.Hotel(
                    name=name,
                    code=code,
                    organization_id=1,
                    city_id=1,
                    region_id=1,
                    branding_settings={"primary_color": "#0B4A3A", "logo_url": ""},
                    is_active=True
                )
                db.add(hotel)
                db.flush()
                print(f"Added Hotel: {name} ({code})")
            db_hotels[code] = hotel
        db.commit()

        # 2. Import unique Departments (Ana Kategori)
        print("\n2. Importing Departments...")
        unique_depts = df_mappings['Ana Kategori'].dropna().unique()
        db_depts = {}
        for name in unique_depts:
            dept = db.query(models.Department).filter_by(name=name).first()
            if not dept:
                # Generate a code: lowercase and alphanumeric only
                code = "".join(c for c in name.upper() if c.isalnum() or c == "_")[:15]
                # Avoid duplicates
                existing_dept_code = db.query(models.Department).filter_by(code=code).first()
                if existing_dept_code:
                    code = f"{code[:12]}_{np.random.randint(10,99)}"
                dept = models.Department(
                    name=name,
                    code=code,
                    is_active=True
                )
                db.add(dept)
                db.flush()
                print(f"Added Department: {name} ({code})")
            db_depts[name] = dept
        db.commit()

        # 3. Import Hotel-Department-Position mappings
        print("\n3. Importing Position Mappings...")
        db.query(models.HotelDepartmentPositionMapping).delete()
        db.commit()
        
        existing_mappings = set()
        
        mapping_count = 0
        new_mappings = []
        for idx, row in df_mappings.iterrows():
            otel_code = row['Otel']
            dept_name = row['Ana Kategori']
            pos_title = row['Tanim (Pozisyon/Isim/Grade)']
            
            if pd.isna(otel_code) or pd.isna(dept_name) or pd.isna(pos_title):
                continue
                
            hotel = db_hotels.get(otel_code)
            dept = db_depts.get(dept_name)
            
            if hotel and dept:
                pos_title = str(pos_title).strip()
                key = (hotel.id, dept.id, pos_title)
                if key not in existing_mappings:
                    mapping = models.HotelDepartmentPositionMapping(
                        hotel_id=hotel.id,
                        department_id=dept.id,
                        position_title=pos_title
                    )
                    new_mappings.append(mapping)
                    existing_mappings.add(key)
                    mapping_count += 1
                    
        db.bulk_save_objects(new_mappings)
        db.commit()
        print(f"Total mappings imported: {mapping_count}")

        # 4. Import Headcount Budgets
        print("\n4. Importing Headcount Budgets...")
        budget_count = 0
        
        # Clear existing budgets to prevent duplicates and keep a clean slate
        db.query(models.WorkforceHeadcountBudget).delete()
        db.commit()
        
        existing_budgets = set()
        new_budgets = []
        
        for idx, row in df_budgets.iterrows():
            otel_code = row['Otel']
            dept_name = row['Ana Kategori']
            pos_title = row['Tanim (Pozisyon/Isim/Grade)']
            budget_val = row['Butce']
            
            if pd.isna(otel_code) or pd.isna(dept_name) or pd.isna(pos_title) or pd.isna(budget_val):
                continue
                
            hotel = db_hotels.get(otel_code)
            dept = db_depts.get(dept_name)
            
            if hotel and dept:
                pos_title = str(pos_title).strip()
                try:
                    budget_num = int(budget_val)
                except ValueError:
                    continue
                
                key = (hotel.id, dept.id, pos_title)
                if key not in existing_budgets:
                    b_entry = models.WorkforceHeadcountBudget(
                        hotel_id=hotel.id,
                        department_id=dept.id,
                        position_title=pos_title,
                        headcount_budget=budget_num,
                        currency="TRY"
                    )
                    new_budgets.append(b_entry)
                    existing_budgets.add(key)
                    budget_count += 1
                    
        db.bulk_save_objects(new_budgets)
        db.commit()
        print(f"Total headcount budgets imported: {budget_count}")
        print("\n--- Excel Import completed successfully! ---")
    except Exception as e:
        db.rollback()
        print(f"Error importing excel data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    import_data()
