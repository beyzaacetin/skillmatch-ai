import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(25):
    sys.stdout.write(f"{i+1}: {lines[i]}")
