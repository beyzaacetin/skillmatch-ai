app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add ref state
target_state = "const showCandidateDrawer = ref(false);"
replacement_state = "const showNewDropdown = ref(false);\n    const showCandidateDrawer = ref(false);"

# Add to return
target_return = "showCandidateDrawer, drawerCandidate, openCandidateDrawer, closeCandidateDrawer, openCandidateProfileFromDrawer,"
replacement_return = "showNewDropdown, showCandidateDrawer, drawerCandidate, openCandidateDrawer, closeCandidateDrawer, openCandidateProfileFromDrawer,"

if target_state in content and target_return in content:
    content = content.replace(target_state, replacement_state)
    content = content.replace(target_return, replacement_return)
    print("showNewDropdown patch successful!")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
else:
    print("State or Return targets not found in app.js")
