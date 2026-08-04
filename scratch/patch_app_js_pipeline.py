import sys

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Add dashboardPipeline ref declaration
target_ref = "const dashboardRecentActivity = ref([]);"
new_refs = "const dashboardRecentActivity = ref([]);\n    const dashboardPipeline = ref([]);"
js_modified = js.replace(target_ref, new_refs, 1)

# 2. Add dashboardPipeline fetch
target_fetch = "dashboardRecentActivity.value = await api('GET', '/api/dashboard/recent-activity');"
new_fetch = """dashboardRecentActivity.value = await api('GET', '/api/dashboard/recent-activity');
        dashboardPipeline.value = await api('GET', '/api/dashboard/pipeline');"""
js_modified = js_modified.replace(target_fetch, new_fetch, 1)

# 3. Add to return statement
target_ret = "dashboardRecentActivity,"
new_ret = "dashboardRecentActivity, dashboardPipeline,"
js_modified = js_modified.replace(target_ret, new_ret, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(js_modified)

print("app.js successfully patched with dashboardPipeline API call")
