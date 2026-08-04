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
    print(f"Deep AI tab found starting at line {start_idx+1}")
    # Print next 80 lines
    for i in range(start_idx, min(len(lines), start_idx + 80)):
        sys.stdout.write(f"{i+1}: {lines[i]}")
else:
    print("Deep AI tab not found")
