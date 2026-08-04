import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# Let's search for "const " and print lines containing "const " and "=>" or "function"
lines = js.split("\n")
print("Function patterns found:")
count = 0
for idx, line in enumerate(lines):
    if ("const " in line or "async " in line) and ("=>" in line or "function" in line or "fetch" in line or "load" in line):
        print(f"Line {idx+1}: {line.strip()[:140]}")
        count += 1
        if count > 40:
            break
