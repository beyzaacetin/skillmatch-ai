import sys
sys.stdout.reconfigure(encoding='utf-8')
ai_helper_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\services\ai_helper.py"
with open(ai_helper_path, "r", encoding="utf-8") as f:
    content = f.read()

import re
funcs = re.findall(r'def \w+\(.*?\):', content)
print("Functions in ai_helper.py:")
for func in funcs[:25]:
    print(func)
