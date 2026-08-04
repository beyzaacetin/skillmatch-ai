import sys

sys.stdout.reconfigure(encoding='utf-8')

pos_router_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\routers\positions.py"

with open(pos_router_path, "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("ai-insights")
if idx != -1:
    print(content[idx-50:idx+1500])
else:
    print("ai-insights endpoint not found")
