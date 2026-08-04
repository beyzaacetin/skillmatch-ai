import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

import re

# Find divs with v-if="workspaceTab === '...'"
matches = re.finditer(r'<div v-if="workspaceTab === \'([^\']+)\'"', html)
positions = []
for m in matches:
    positions.append((m.group(1), m.start()))

positions.sort(key=lambda x: x[1])

for i in range(len(positions)):
    name, start = positions[i]
    end = positions[i+1][1] if i + 1 < len(positions) else len(html)
    tab_html = html[start:end]
    # Keep only first 20 lines of the tab HTML for overview
    lines = tab_html.split("\n")
    print(f"=== Tab '{name}' (starts at line index {start}, total lines: {len(lines)}) ===")
    for line in lines[:15]:
        print(line.encode('ascii', errors='replace').decode('ascii'))
    print("...\n")
