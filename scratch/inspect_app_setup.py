import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# Let's find where return statement starts inside setup()
# Normally it's near the end of setup
# Let's search for "return {"
import re
matches = list(re.finditer(r'return\s*\{', js))
if matches:
    start = matches[-1].start()
    print("Found return statement at", start)
    print(js[start:start+1500])
else:
    print("No return statement found")
