import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Searching for page routing checks (e.g., page === )...")
for idx, line in enumerate(lines):
    if "page === " in line or 'page ===' in line or "v-if=\"page" in line:
        text = line.strip()[:140]
        sys.stdout.write(f"Line {idx+1}: {text.encode('ascii', errors='replace').decode('ascii')}\n")
