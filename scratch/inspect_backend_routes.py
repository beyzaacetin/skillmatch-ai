import sys

sys.stdout.reconfigure(encoding='utf-8')

main_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\main.py"

with open(main_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find include_router lines
import re
matches = re.finditer(r'app\.include_router\([^)]+\)', content)
print("Registered routers:")
for m in matches:
    print(m.group(0))
