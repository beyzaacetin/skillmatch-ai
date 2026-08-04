import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

matches = list(re.finditer(r'dashboard/summary', js))
for m in matches:
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 500)
    print("MATCH:")
    print(js[start:end])
    print("="*60)
