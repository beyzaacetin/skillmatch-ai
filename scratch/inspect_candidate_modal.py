import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's find the start of candidate modal
start_idx = -1
for idx, line in enumerate(lines):
    if 'class="overlay"' in line and 'selectedCandidate' in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"Found candidate modal starting at line {start_idx+1}")
    # print 120 lines
    for i in range(start_idx, min(len(lines), start_idx + 150)):
        # print with line number
        sys.stdout.write(f"{i+1}: {lines[i]}")
else:
    print("Candidate modal not found")
