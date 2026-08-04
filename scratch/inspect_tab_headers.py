import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for '<div class="tabs"' and read everything until the closing div
matches = re.finditer(r'<div class="tabs"[^>]*>', html)
for m in matches:
    start = m.start()
    # Find closing div
    # simple stack based search
    depth = 1
    idx = m.end()
    while idx < len(html) and depth > 0:
        if html[idx:idx+4] == "<div":
            depth += 1
            idx += 4
        elif html[idx:idx+6] == "</div&": # wait or just </div
            pass
        elif html[idx:idx+6] == "</div>":
            depth -= 1
            idx += 6
        else:
            idx += 1
    print(f"Tabs block:\n{html[start:idx]}")
    print("=" * 50)
