import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Find all blocks of the form:
# <div v-if="workspaceTab === '...'">
# up to its closing tag or next tab div
matches = list(re.finditer(r'<div v-if="workspaceTab === \'([^\']+)\'"', html))
print(f"Found {len(matches)} tabs:")
for i, m in enumerate(matches):
    name = m.group(1)
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else len(html)
    tab_html = html[start:end]
    print(f"Tab name: {name}, start index: {start}, end index: {end}, length: {len(tab_html)}")
