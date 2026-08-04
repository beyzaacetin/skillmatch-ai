index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Start tag
start_tag = '<template v-if="page===\'jobs\'">'
# End tag - start of position workspace:
end_tag = '<!-- POSITION WORKSPACE -->'

start_idx = html.find(start_tag)
end_idx = html.find(end_tag)

if start_idx != -1 and end_idx != -1:
    before = html[:start_idx]
    after = html[end_idx:]
    
    jobs_html = """<template v-if="page==='jobs'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Positions</div>
          <div class="page-hdr-sub">Manage active job openings and recruitment goals</div>
        </div>
        <div style="margin-left:auto; display:flex; gap:12px; align-items:center;">
          <div class="search-bar" style="height:36px; display:flex; align-items:center; gap:8px; background:var(--g100); border-radius:12px; padding:0 12px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="candidateSearch" placeholder="Search positions..." style="border:none; background:transparent; outline:none; font-size:12.5px; width:100%;">
          </div>
          <button class="btn btn-secondary btn-sm" style="height:36px; border-radius:12px;" @click="alert('Filters: Status, department, priority.')">Filter</button>
          <button class="btn btn-primary btn-sm" style="height:36px; border-radius:12px;" @click="showNewPositionModal=true">Create Position</button>
        </div>
      </div>

      <div class="page-body">
        <!-- Top KPI Cards -->
        <div style="margin-bottom:24px; display:grid; grid-template-columns:repeat(4, 1fr); gap:16px;">
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Total Positions</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ positions.length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Active</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ positions.filter(p => p.status === 'open').length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Total Candidates</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ candidates.length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Avg Time To Hire</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">24d</div>
          </div>
        </div>

        <!-- Positions Table -->
        <div class="card" style="overflow:hidden; border-radius:16px; box-shadow:var(--sh);">
          <table class="tbl" style="width:100%; border-collapse:collapse;">
            <thead>
              <tr style="background:var(--bg);">
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Position</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Status</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Priority</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Candidates</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Headcount</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Hiring Manager</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Target Date</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; width:150px;">Progress</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in positions" :key="p.id" @click="viewPositionWorkspace(p)" style="cursor:pointer; transition: background 0.15s;" class="table-row">
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <div style="font-weight:700; color:var(--text-primary); font-size:13.5px;">{{ p.title }}</div>
                  <div style="font-size:12px; color:var(--text-secondary);">{{ p.department }}</div>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <span class="badge" :class="p.status === 'open' ? 'b-hired' : 'b-rejected'">{{ p.status === 'open' ? 'ACTIVE' : 'CLOSED' }}</span>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <span class="badge" style="background:#fef2f2; color:#b91c1c; font-weight:700;">HIGH</span>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-primary);">
                  {{ candidates.filter(c=>c.position_id===p.id).length }} candidates
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-primary); font-weight:600;">
                  {{ p.openings || 1 }} openings
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-primary);">
                  {{ p.hiring_manager || 'Sarah Mitchell' }}
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-secondary); font-size:13px;">
                  Sep 1, 2024
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:8px;">
                    <div style="flex:1; height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                      <div style="width:66%; height:100%; background:var(--primary); border-radius:3px;"></div>
                    </div>
                    <span style="font-size:12px; font-weight:700; color:var(--primary);">66%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
"""
    
    html = before + jobs_html + after
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Positions List page patched successfully!")
else:
    print("Jobs template tag not found!")
