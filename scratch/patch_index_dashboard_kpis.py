import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if '<!-- Top KPI Cards -->' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find Top KPI Cards start line")
    sys.exit(1)

# Find the end of this KPI block (the closing div)
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if '<!-- Dashboard Main Area: Charts -->' in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Failed to find Dashboard Main Area: Charts line")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of KPI Cards block")
    sys.exit(1)

print(f"Replacing KPI block from line {start_idx+1} to {closing_div_idx+1}")

new_kpi_html = """        <!-- Top KPI Cards -->
        <div style="margin-bottom:24px; display:grid; grid-template-columns:repeat(6, 1fr); gap:16px;">
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Open Positions</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ dashboardSummary.total_positions || 0 }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Total Candidates</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ dashboardSummary.total_candidates || 0 }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Interviews This Week</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ dashboardSummary.interviews_this_week || 0 }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Time To Hire</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ dashboardSummary.time_to_hire || 'N/A' }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Offer Acceptance</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ dashboardSummary.offer_acceptance || 'N/A' }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Hiring Velocity</div>
            <div style="font-size:24px; font-weight:700; color:var(--primary);">{{ dashboardSummary.hiring_velocity || 'N/A' }}</div>
          </div>
        </div>
"""

lines[start_idx:closing_div_idx+1] = [new_kpi_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html Dashboard KPIs successfully patched")
