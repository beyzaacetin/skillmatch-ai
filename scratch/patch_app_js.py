import os

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """async function viewPositionWorkspace(pos) {
      selectedPosition.value = pos;
      workspaceTab.value = 'overview';
      page.value = 'position_workspace';
      matchingLoading.value = true;
      workspaceAiGuide.value = pos.ai_criteria_guide;
      currentHrStep.value = 0;
      currentTechStep.value = 0;
      try {
        await loadPositionStats(pos.id);
        const res = await api('GET', `/api/matches/position/${pos.id}`);
        matchingResults.value = res;
        await loadAutomationRules();
      } catch (err) {
        console.error("Match error:", err);
      }
      matchingLoading.value = false;
    }"""

replacement = """async function loadPositionAiInsights(posId) {
      workspaceAiInsightsLoading.value = true;
      try {
        workspaceAiInsights.value = await api('GET', `/api/positions/${posId}/ai-insights`);
      } catch (e) {
        console.error("Insights load failed:", e);
      }
      workspaceAiInsightsLoading.value = false;
    }

async function viewPositionWorkspace(pos) {
      selectedPosition.value = pos;
      workspaceTab.value = 'overview';
      page.value = 'position_workspace';
      matchingLoading.value = true;
      workspaceAiGuide.value = pos.ai_criteria_guide;
      currentHrStep.value = 0;
      currentTechStep.value = 0;
      try {
        await loadPositionStats(pos.id);
        const res = await api('GET', `/api/matches/position/${pos.id}`);
        matchingResults.value = res;
        await loadAutomationRules();
        await loadPositionAiInsights(pos.id);
      } catch (err) {
        console.error("Match error:", err);
      }
      matchingLoading.value = false;
    }"""

if target in content:
    content = content.replace(target, replacement)
    print("Replacement successful!")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
else:
    print("Target string not found in app.js!")
