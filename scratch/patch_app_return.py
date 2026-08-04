app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

target = "workspaceTab, workspaceStats, workspaceAiGuide, workspaceAiGuideLoading, automationRules, showPassiveCandidates,"
replacement = "workspaceTab, workspaceStats, workspaceAiGuide, workspaceAiGuideLoading, automationRules, showPassiveCandidates, workspaceAiInsights, workspaceAiInsightsLoading, collapsedStages, toggleStageCollapse, showCandidateDrawer, drawerCandidate, openCandidateDrawer, closeCandidateDrawer, openCandidateProfileFromDrawer,"

if target in content:
    content = content.replace(target, replacement)
    print("Return block patch successful!")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
else:
    print("Target not found in return block of app.js")
