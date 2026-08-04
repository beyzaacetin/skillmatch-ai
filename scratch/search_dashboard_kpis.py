import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's find "dashboard" and print the next 60 lines
start_idx = -1
for idx, line in enumerate(lines):
    if "page==='dashboard'" in line or 'page === \'dashboard\'' in line or 'page===\'dashboard\'' in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"Found dashboard page template starting at line {start_idx+1}")
    for i in range(start_idx, min(len(lines), start_idx + 80)):
        sys.stdout.write(f"{i+1}: {lines[i]}")
else:
    print("Dashboard not found")
