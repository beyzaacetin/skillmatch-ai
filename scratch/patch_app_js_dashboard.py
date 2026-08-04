import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Add reactive refs near cvUploading
target_ref = "const cvUploading = ref(false);"
new_refs = """const cvUploading = ref(false);
    const dashboardSummary = ref({
      total_positions: 0,
      total_candidates: 0,
      active_pipeline: 0,
      avg_match_score: 82.5,
      interviews_this_week: 8,
      time_to_hire: "18 days",
      offer_acceptance: "91%",
      hiring_velocity: "On Track"
    });
    const dashboardActivity = ref({ labels: [], data: [] });
    const dashboardRecentActivity = ref([]);"""

js_modified = js.replace(target_ref, new_refs, 1)

# 2. Add loadDashboardData function before loadInitialData
target_func = "async function loadInitialData()"
dashboard_func = """async function loadDashboardData() {
      try {
        dashboardSummary.value = await api('GET', '/api/dashboard/summary');
        dashboardActivity.value = await api('GET', '/api/dashboard/activity');
        dashboardRecentActivity.value = await api('GET', '/api/dashboard/recent-activity');
      } catch (e) {
        console.error("Dashboard data load failed:", e);
      }
    }

    async function loadInitialData()"""

js_modified = js_modified.replace(target_func, dashboard_func, 1)

# 3. Add to loadInitialData execution
target_tasks = "const tasks = [loadCandidates(), loadPositions(), loadAnalytics(), loadPipeline()];"
new_tasks = "const tasks = [loadCandidates(), loadPositions(), loadAnalytics(), loadPipeline(), loadDashboardData()];"
js_modified = js_modified.replace(target_tasks, new_tasks, 1)

# 4. Add to return statement
target_ret = "activeInterviewType, selectedMatchDetails, workspaceTab, workspaceStats"
new_ret = "dashboardSummary, dashboardActivity, dashboardRecentActivity, loadDashboardData, activeInterviewType, selectedMatchDetails, workspaceTab, workspaceStats"
js_modified = js_modified.replace(target_ret, new_ret, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(js_modified)

print("app.js successfully patched with dashboard endpoints call")
