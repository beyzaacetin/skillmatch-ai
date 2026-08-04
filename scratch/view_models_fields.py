import sys

sys.stdout.reconfigure(encoding='utf-8')

models_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\models.py"

with open(models_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's inspect class structures
classes = ["class User", "class Position", "class Candidate", "class Application", "class Interview", "class MatchScore", "class RecruitmentTask"]

for cls in classes:
    start = content.find(cls)
    if start != -1:
        # print first 35 lines of this class
        lines = content[start:].split("\n")[:40]
        print(f"=== {cls} ===")
        print("\n".join(lines))
        print("="*50)
