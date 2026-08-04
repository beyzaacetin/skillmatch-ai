import sys

sys.stdout.reconfigure(encoding='utf-8')

pos_router_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\routers\positions.py"

with open(pos_router_path, "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("get_position_ai_insights")
if idx != -1:
    lines = content[idx:].split("\n")
    print("\n".join(lines[:45]))
