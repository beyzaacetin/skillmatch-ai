import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's search for the tabs div in position_workspace
for idx, line in enumerate(lines):
    if 'class="tabs"' in line and 'workspaceTab ===' in lines[idx+1]:
        print(f"Tabs block found at line {idx+1}")
        for i in range(idx, idx+16):
            sys.stdout.write(f"{i+1}: {lines[i]}")
        break
