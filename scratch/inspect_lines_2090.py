import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"backend/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(2080, min(2110, len(lines))):
    sys.stdout.write(f"{i+1}: {lines[i]}")
