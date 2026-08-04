import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

import re
matches = list(re.finditer(r'drawerCandidate|showCandidateDrawer', html))
print(f"Total drawer references in index.html: {len(matches)}")
for m in matches:
    start = max(0, m.start() - 50)
    end = min(len(html), m.end() + 100)
    snippet = html[start:end].strip().replace("\n", " ")
    print(f"Match: {snippet.encode('ascii', errors='replace').decode('ascii')}")
