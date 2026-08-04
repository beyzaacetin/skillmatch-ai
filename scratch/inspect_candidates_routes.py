import sys

sys.stdout.reconfigure(encoding='utf-8')

cand_routes_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\routers\candidates.py"

with open(cand_routes_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's find save-hr-answers and save-tech-answers
funcs = ["save_hr_answers", "save_tech_answers", "generate_hr_questions", "generate_tech_questions", "generate_dossier", "update_candidate"]

for fn in funcs:
    idx = content.find(fn)
    if idx != -1:
        print(f"=== {fn} ===")
        # print first 35 lines
        lines = content[idx-5:idx+800].split("\n")
        print("\n".join(lines[:35]))
        print("="*60)
    else:
        print(f"Route for {fn} not found")
