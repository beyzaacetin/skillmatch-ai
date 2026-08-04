import os
import sys

# Set standard output to handle utf-8 if possible, or print with replacement
sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

if not os.path.exists(index_path):
    print("index.html not found at:", index_path)
    exit(1)

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Searching for workspaceTab references...")
for idx, line in enumerate(lines):
    if "workspaceTab" in line:
        text = line.strip()[:120]
        # print with error handling
        sys.stdout.write(f"Line {idx+1}: {text.encode('ascii', errors='replace').decode('ascii')}\n")
