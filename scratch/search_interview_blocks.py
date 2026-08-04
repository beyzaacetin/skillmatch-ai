import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if "workspaceTab === 'hr_interview'" in line:
        start_idx = idx
        break

end_idx = -1
for idx, line in enumerate(lines):
    if "workspaceTab === 'final_decision'" in line:
        end_idx = idx
        break

if start_idx != -1 and end_idx != -1:
    print(f"hr_interview starts at line {start_idx+1}")
    print(f"final_decision starts at line {end_idx+1}")
    # Find the closing div of tech_interview
    closing_div_idx = -1
    for i in range(end_idx - 1, start_idx, -1):
        if "</div>" in lines[i]:
            closing_div_idx = i
            break
    print(f"Closing div of tech_interview is at line {closing_div_idx+1}")
else:
    print("Failed to find interview blocks")
