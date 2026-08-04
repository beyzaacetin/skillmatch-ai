import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

idx = js.find("const filteredCandidates = computed(() => {")
if idx != -1:
    print(js[idx-100:idx+400])
else:
    print("filteredCandidates not found")
