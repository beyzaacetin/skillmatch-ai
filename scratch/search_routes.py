import os
import re

backend_dir = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend"

print("Searching for routes in backend...")
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "dashboard" in content or "summary" in content or "pipeline" in content:
                for line_idx, line in enumerate(content.split("\n")):
                    if "@router." in line or "def " in line:
                        if any(x in line for x in ["summary", "activity", "pipeline", "recent", "stats"]):
                            print(f"{file}:{line_idx+1}: {line.strip()}")
