import sys
sys.stdout.reconfigure(encoding='utf-8')
js_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    html = f.read()

import re
matches = list(re.finditer(r'drawer|Drawer', html))
print(f"Total drawer references in app.js: {len(matches)}")
for m in matches:
    start = max(0, m.start() - 50)
    end = min(len(html), m.end() + 100)
    snippet = html[start:end].strip().replace("\n", " ")
    print(f"Match: {snippet.encode('ascii', errors='replace').decode('ascii')}")
