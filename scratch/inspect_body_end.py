import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines[-50:]):
    print(f"{len(lines)-50+idx+1}: {line.strip()}")
