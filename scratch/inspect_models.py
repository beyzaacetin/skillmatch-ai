import sys

sys.stdout.reconfigure(encoding='utf-8')

models_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\models.py"

with open(models_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "class " in line:
        print(f"Line {idx+1}: {line.strip()}")
