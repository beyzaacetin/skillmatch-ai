import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for workspaceTab button group.
# Look for something like workspaceTab = 'overview'
matches = re.finditer(r'@click="workspaceTab\s*=\s*\'([^\']+)\'"', html)
for m in matches:
    # Print the button element containing it, back 50 chars and forward 50 chars
    start = max(0, m.start() - 60)
    end = min(len(html), m.end() + 60)
    snippet = html[start:end]
    print("Found button trigger:")
    print(snippet.strip())
    print("-" * 40)
