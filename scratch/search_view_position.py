import sys
sys.stdout.reconfigure(encoding='utf-8')
app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "async function viewPositionWorkspace" in line:
        # print 35 lines around it
        start = max(0, idx - 2)
        end = min(len(lines), idx + 35)
        for i in range(start, end):
            sys.stdout.write(f"{i+1}: {lines[i].encode('ascii', errors='replace').decode('ascii')}")
        break
