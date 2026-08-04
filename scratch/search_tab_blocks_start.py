import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"backend/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "workspaceTab ===" in line or "workspaceTab ===" in line:
        print(f"Line {idx+1}: {line.strip()[:120]}")
