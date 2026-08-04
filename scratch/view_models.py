import sys
sys.stdout.reconfigure(encoding='utf-8')
models_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\models.py"
with open(models_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's extract class names and column definitions
import re
classes = re.findall(r'class \w+\(.*?\):', content)
print("Found classes:")
for c in classes:
    print(c)

# Let's print candidate and position model columns
lines = content.split("\n")
cand_lines = []
pos_lines = []
app_lines = []
in_cand = False
in_pos = False
in_app = False

for line in lines:
    if "class Candidate(" in line or "class Candidate_v" in line:
        in_cand = True
        cand_lines.append(line)
        continue
    if "class Position(" in line:
        in_pos = True
        pos_lines.append(line)
        continue
    if "class Application(" in line:
        in_app = True
        app_lines.append(line)
        continue
        
    if in_cand:
        if line.startswith("class ") or line.strip() == "":
            if not line.startswith("    "):
                in_cand = False
        else:
            cand_lines.append(line)
            
    if in_pos:
        if line.startswith("class ") or line.strip() == "":
            if not line.startswith("    "):
                in_pos = False
        else:
            pos_lines.append(line)

    if in_app:
        if line.startswith("class ") or line.strip() == "":
            if not line.startswith("    "):
                in_app = False
        else:
            app_lines.append(line)

print("\n--- Candidate Model ---")
for line in cand_lines[:30]:
    sys.stdout.write(line.encode('ascii', errors='replace').decode('ascii') + "\n")

print("\n--- Position Model ---")
for line in pos_lines[:30]:
    sys.stdout.write(line.encode('ascii', errors='replace').decode('ascii') + "\n")

print("\n--- Application Model ---")
for line in app_lines[:30]:
    sys.stdout.write(line.encode('ascii', errors='replace').decode('ascii') + "\n")
