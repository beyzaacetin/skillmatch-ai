import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

matches = list(re.finditer(r'computed\(', js))
for m in matches[:10]:
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 250)
    print(js[start:end].strip().replace('\n', ' '))
    print("-" * 40)
