import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for "candidate" pages, e.g. v-if="page === 'candidate_profile'" or similar
matches = re.finditer(r'page\s*===\s*\'[^\']+\'', html)
for m in matches:
    print(m.group(0))

print("\nSearch for selectedCandidate in templates...")
# Let's search for occurrences of "selectedCandidate" in index.html, showing line numbers
lines = html.split("\n")
for idx, line in enumerate(lines):
    if "selectedCandidate" in line and ("profile" in line.lower() or "page" in line.lower() or "tab" in line.lower()):
        print(f"Line {idx+1}: {line.strip()[:120]}")
