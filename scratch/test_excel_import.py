import pandas as pd
import io

df = pd.DataFrame(columns=[
    'otel', 'otel_alt', 'ana kategori', 'alt kategori', 
    'tanım (pozisyon/isim/grade)', 'monthofyear', 'toplam fte', 'bütçe'
])

df.columns = [str(c).strip().lower() for c in df.columns]

col_mappings = {
    "hotel": ["hotel name", "hotel", "otel", "otel adı", "otel_alt"],
    "department": ["department", "departman", "bölüm", "ana kategori", "ana_kategori"],
    "position": ["position", "position title", "pozisyon", "unvan", "tanım (pozisyon/isim/grade)", "tanım", "tanim"],
    "budget": ["headcount budget", "budget", "bütçe", "kontenjan", "headcount", "toplam fte", "toplam_fte"],
    "salary_min": ["target salary min", "salary min", "min maaş", "minimum maaş", "salary_min"],
    "salary_max": ["target salary max", "salary max", "max maaş", "maksimum maaş", "salary_max"],
    "currency": ["currency", "para birimi", "döviz"]
}

def find_col(key):
    for col in df.columns:
        if col in col_mappings[key]:
            return col
    return None

hotel_col = find_col("hotel")
dept_col = find_col("department")
pos_col = find_col("position")
budget_col = find_col("budget")

if not hotel_col or not dept_col or not pos_col or not budget_col:
    print("RESULT: MATCH FAILED!")
else:
    print("RESULT: MATCH SUCCESSFUL!")
