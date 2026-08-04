import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# Match async function ... or function ...
matches = re.finditer(r'(async\s+)?function\s+(\w+)\s*\(', js)
print("Functions in app.js:")
for m in matches:
    print(f"Name: {m.group(2)}, is_async: {bool(m.group(1))}")
