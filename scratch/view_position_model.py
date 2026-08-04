import sys

sys.stdout.reconfigure(encoding='utf-8')

models_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\models.py"

with open(models_path, "r", encoding="utf-8") as f:
    content = f.read()

start = content.find("class Position")
if start != -1:
    lines = content[start:].split("\n")[:50]
    print("\n".join(lines))
else:
    print("class Position not found")
