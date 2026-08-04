import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if "v-if=\"workspaceTab === 'deep_ai'\"" in line or 'v-if="workspaceTab === \'deep_ai\'"' in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"Deep AI tab found at line {start_idx+1}")
    # Let's find where the next tab starts
    end_idx = -1
    for i in range(start_idx+1, len(lines)):
        if "workspaceTab === 'hr_interview'" in lines[i] or "workspaceTab === 'interviews'" in lines[i]:
            end_idx = i
            break
    
    closing_div_idx = -1
    for i in range(end_idx-1, start_idx, -1):
        if "</div>" in lines[i]:
            closing_div_idx = i
            break
    print(f"Ending closing div of deep_ai is at line {closing_div_idx+1}")
