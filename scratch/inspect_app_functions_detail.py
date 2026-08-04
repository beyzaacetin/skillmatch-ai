import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

funcs = [
    "async function loadPositionAiInsights",
    "async function generateFinalDossier",
    "async function saveRecruiterEvaluation",
    "async function startHrQuestions",
    "async function saveHrAnswers",
    "async function startTechQuestions",
    "async function saveTechAnswers"
]

for fn in funcs:
    idx = js.find(fn)
    if idx != -1:
        # Find closing brace by matching brackets
        # Let's print the first 1000 characters from function start
        print(f"=== {fn} ===")
        print(js[idx:idx+800])
        print("="*60)
    else:
        print(f"Function {fn} not found")
