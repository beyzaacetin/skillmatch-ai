import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
cand_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\routers\candidates.py"
with open(cand_path, "r", encoding="utf-8") as f:
    content = f.read()

print("Routes in candidates.py:")
for line_idx, line in enumerate(content.split("\n")):
    if "@router." in line or "def " in line:
        if any(x in line for x in ["get", "post", "put", "delete", "patch", "upload"]):
            sys.stdout.write(f"Line {line_idx+1}: {line.strip()}\n")
