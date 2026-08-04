import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Insert activeInterviewType declaration
target_decl = "const currentHrStep = ref(0);"
new_decl = "const currentHrStep = ref(0);\n    const activeInterviewType = ref('hr');"
js_modified = js.replace(target_decl, new_decl, 1)

# 2. Add to return statement
target_ret = "selectedMatchDetails, workspaceTab, workspaceStats"
new_ret = "activeInterviewType, selectedMatchDetails, workspaceTab, workspaceStats"
js_modified = js_modified.replace(target_ret, new_ret, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(js_modified)

print("app.js successfully patched with activeInterviewType")
