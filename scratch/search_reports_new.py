import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if "v-if=\"workspaceTab === 'reports'\"" in line or 'v-if="workspaceTab === \'reports\'"' in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"reports found starting at line {start_idx+1}")
    # Find next tab
    end_idx = -1
    for i in range(start_idx+1, len(lines)):
        if "workspaceTab === 'calendar'" in lines[i]:
            end_idx = i
            break
    closing_div_idx = -1
    for i in range(end_idx-1, start_idx, -1):
        if "</div>" in lines[i]:
            closing_div_idx = i
            break
    print(f"Closing div of reports is at line {closing_div_idx+1}")
else:
    print("reports tab not found")
