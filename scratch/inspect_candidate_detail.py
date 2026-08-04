import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

import re
matches = list(re.finditer(r'selectedCandidate', html))
print(f"Total selectedCandidate occurrences: {len(matches)}")

# Let's search for selectedCandidate modal or detail view
for m in re.finditer(r'<div[^>]*v-if="[^"]*selectedCandidate[^"]*"', html):
    start = m.start()
    print(f"Found match starting at {start}: {html[start:start+120].strip().encode('ascii', errors='replace').decode('ascii')}")
