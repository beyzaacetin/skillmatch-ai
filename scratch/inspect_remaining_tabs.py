import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

matches = list(re.finditer(r'<div v-if="workspaceTab === \'([^\']+)\'"', html))
tabs_to_inspect = ['matches', 'deep_ai', 'hr_interview', 'tech_interview', 'final_decision', 'reports']

for i, m in enumerate(matches):
    name = m.group(1)
    if name in tabs_to_inspect:
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(html)
        tab_html = html[start:end]
        print(f"=== TAB: {name} ({len(tab_html)} chars) ===")
        # Print first 400 chars and last 400 chars
        print("START:")
        print(tab_html[:1500])
        print("...")
        print("END:")
        print(tab_html[-800:])
        print("="*60)
