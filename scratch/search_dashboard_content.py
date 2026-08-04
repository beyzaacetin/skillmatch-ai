import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's search for template checks of dashboard
start_idx = -1
for idx, line in enumerate(lines):
    if "template v-if=\"page==='dashboard'\"" in line or "template v-if=\"page === 'dashboard'\"" in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"Found template dashboard starting at line {start_idx+1}")
    for i in range(start_idx, min(len(lines), start_idx + 80)):
        sys.stdout.write(f"{i+1}: {lines[i]}")
else:
    print("Dashboard template not found")
