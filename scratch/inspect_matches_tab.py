import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's print around line 983 in index.html (line 983-1045)
for i in range(975, 1045):
    if i < len(lines):
        sys.stdout.write(f"{i+1}: {lines[i].encode('ascii', errors='replace').decode('ascii')}")
