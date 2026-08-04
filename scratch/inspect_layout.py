import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Find the first 3000 characters to see the top structure
print("--- Top Layout Structure (Index.html) ---")
lines = html.split("\n")
for idx, line in enumerate(lines[:120]):
    sys.stdout.write(f"Line {idx+1}: {line.strip()[:140].encode('ascii', errors='replace').decode('ascii')}\n")
