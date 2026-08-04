import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Insert computed property
target_comp = "// ─── COMPUTED ─────────────────────────────────────────────────────"
new_comp = """// ─── COMPUTED ─────────────────────────────────────────────────────
    const selectedMatchDetails = computed(() => {
      if (!selectedCandidate.value || !positionMatches.value || !positionMatches.value.length) return null;
      // Note: matches returned by API can be flat or nested, check both
      return positionMatches.value.find(m => {
        if (m.candidate && m.candidate.id === selectedCandidate.value.id) return true;
        if (m.id === selectedCandidate.value.id) return true;
        return false;
      }) || null;
    });
"""

js_modified = js.replace(target_comp, new_comp, 1)

# 2. Add to return statement
target_ret = "workspaceTab, workspaceStats"
new_ret = "selectedMatchDetails, workspaceTab, workspaceStats"
js_modified = js_modified.replace(target_ret, new_ret, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(js_modified)

print("app.js successfully patched with computed property selectedMatchDetails")
