import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if '<!-- Right: Recent Activity Feed -->' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find Recent Activity Feed start line")
    sys.exit(1)

# Find the end of this block
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if 'template v-if="page===\'talent\'"' in lines[i] or "page==='talent'" in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Failed to find page==='talent' template line")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of Recent Activity Feed")
    sys.exit(1)

print(f"Replacing Recent Activity block from line {start_idx+1} to {closing_div_idx+1}")

new_activity_html = """          <!-- Right: Recent Activity Feed -->
          <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
            <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Recent Activity</div>
            <div style="display:flex; flex-direction:column; gap:16px;">
              <div v-for="act in dashboardRecentActivity" :key="act.id" style="display:flex; gap:12px;">
                <div style="width:8px; height:8px; border-radius:50%; margin-top:6px; flex-shrink:0;"
                     :style="{ background: act.color === 'green' ? 'var(--green)' : act.color === 'blue' ? 'var(--blue)' : act.color === 'purple' ? 'var(--purple)' : act.color === 'amber' ? 'var(--amber)' : 'var(--g400)' }"></div>
                <div style="flex:1;">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">{{ act.action }}</div>
                  <div style="font-size:11px; color:var(--text-secondary);">{{ act.description }}</div>
                  <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">{{ act.timestamp }}</div>
                </div>
              </div>
              <div v-if="!dashboardRecentActivity.length" style="font-size:12.5px; color:var(--text-secondary); text-align:center; padding:20px;">No recent activities.</div>
            </div>
          </div>
"""

lines[start_idx:closing_div_idx+1] = [new_activity_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html Recent Activity Feed successfully patched")
