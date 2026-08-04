import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

idx = js.find("async function loadPositionMatches")
if idx != -1:
    print(js[idx:idx+600])
else:
    print("loadPositionMatches function not found")
