index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Locate the exact dashboard block start and end
# Start: <template v-if="page==='dashboard'">
# End: <template v-if="page==='talent'">
start_tag = '<template v-if="page===' + "'dashboard'" + '">'
end_tag = '<template v-if="page===' + "'talent'" + '">'

start_idx = html.find(start_tag)
end_idx = html.find(end_tag)

if start_idx != -1 and end_idx != -1:
    before = html[:start_idx]
    after = html[end_idx:]
    
    dashboard_html = """<template v-if="page==='dashboard'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Dashboard</div>
          <div class="page-hdr-sub">Enterprise Recruitment Intelligence Platform</div>
        </div>
        <div style="margin-left:auto; display:flex; gap:10px;">
          <button class="btn btn-primary" @click="showNewPositionModal=true">
            Create Position
          </button>
        </div>
      </div>
      
      <div class="page-body">
        <!-- Top KPI Cards -->
        <div style="margin-bottom:24px; display:grid; grid-template-columns:repeat(6, 1fr); gap:16px;">
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Open Positions</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ positions.filter(p => p.status === 'open').length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Total Candidates</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ candidates.length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Interviews This Week</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">8</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Time To Hire</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">18d</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Offer Acceptance</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">91%</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Hiring Velocity</div>
            <div style="font-size:24px; font-weight:700; color:var(--primary);">On Track</div>
          </div>
        </div>

        <!-- Dashboard Main Area: Charts -->
        <div style="display:grid; grid-template-columns:1.5fr 1fr; gap:24px; margin-bottom:24px;">
          <!-- Left: Hiring Activity Area Chart -->
          <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
            <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Hiring Activity</div>
            <div style="position:relative;">
              <svg viewBox="0 0 500 180" style="width:100%; height:auto; display:block;">
                <defs>
                  <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#0F6B57" stop-opacity="0.2"/>
                    <stop offset="100%" stop-color="#0F6B57" stop-opacity="0.0"/>
                  </linearGradient>
                </defs>
                <!-- Area -->
                <path d="M 0 150 Q 80 110 160 130 T 320 70 T 480 30 L 480 180 L 0 180 Z" fill="url(#chartGrad)" />
                <!-- Line -->
                <path d="M 0 150 Q 80 110 160 130 T 320 70 T 480 30" fill="none" stroke="#0F6B57" stroke-width="3" stroke-linecap="round" />
                <!-- Circles -->
                <circle cx="0" cy="150" r="4" fill="#0F6B57" />
                <circle cx="96" cy="120" r="4" fill="#0F6B57" />
                <circle cx="192" cy="130" r="4" fill="#0F6B57" />
                <circle cx="288" cy="80" r="4" fill="#0F6B57" />
                <circle cx="384" cy="60" r="4" fill="#0F6B57" />
                <circle cx="480" cy="30" r="4" fill="#0F6B57" />
              </svg>
              <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-secondary); margin-top:8px; padding:0 8px;">
                <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span>
              </div>
            </div>
          </div>

          <!-- Right: Pipeline Breakdown -->
          <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
            <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Pipeline Breakdown</div>
            <div style="display:flex; flex-direction:column; gap:12px;">
              <!-- Applied -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>Applied</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'applied').length || 15 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:80%; height:100%; background:var(--blue);"></div>
                </div>
              </div>
              <!-- Screening -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>Screening</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'screening').length || 10 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:60%; height:100%; background:var(--warning);"></div>
                </div>
              </div>
              <!-- HR Interview -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>HR Interview</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'hr_interview').length || 8 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:45%; height:100%; background:var(--purple);"></div>
                </div>
              </div>
              <!-- Technical -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>Technical</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'tech_interview').length || 5 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:30%; height:100%; background:var(--primary);"></div>
                </div>
              </div>
              <!-- Offer -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>Offer</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'offer').length || 3 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:20%; height:100%; background:var(--success);"></div>
                </div>
              </div>
              <!-- Hired -->
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:500;">
                  <span>Hired</span><span style="font-weight:700;">{{ candidates.filter(c => c.status === 'hired').length || 2 }}</span>
                </div>
                <div style="height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                  <div style="width:10%; height:100%; background:var(--primary-hover);"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom Section: Active Positions Table & Activity Feed -->
        <div style="display:grid; grid-template-columns:1.5fr 1fr; gap:24px;">
          <!-- Left: Active Positions Table -->
          <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
            <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Active Positions</div>
            <div style="overflow-x:auto;">
              <table class="tbl" style="width:100%; border-collapse:collapse;">
                <thead>
                  <tr>
                    <th style="padding:12px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Position</th>
                    <th style="padding:12px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Department</th>
                    <th style="padding:12px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Candidates</th>
                    <th style="padding:12px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Stage</th>
                    <th style="padding:12px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in positions.slice(0, 5)" :key="p.id" style="cursor:pointer;" @click="viewPositionWorkspace(p)">
                    <td style="padding:12px; border-bottom:1px solid var(--border); font-weight:600; color:var(--text-primary);">{{ p.title }}</td>
                    <td style="padding:12px; border-bottom:1px solid var(--border); color:var(--text-secondary);">{{ p.department }}</td>
                    <td style="padding:12px; border-bottom:1px solid var(--border); color:var(--text-secondary);">{{ candidates.filter(c=>c.position_id===p.id).length }}</td>
                    <td style="padding:12px; border-bottom:1px solid var(--border);"><span class="badge b-applied">{{ p.status.toUpperCase() }}</span></td>
                    <td style="padding:12px; border-bottom:1px solid var(--border);"><span class="badge" style="background:#fef2f2; color:#b91c1c; font-weight:700;">HIGH</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Right: Recent Activity Feed -->
          <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
            <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Recent Activity</div>
            <div style="display:flex; flex-direction:column; gap:16px;">
              <div style="display:flex; gap:12px;">
                <div style="width:8px; height:8px; border-radius:50%; background:var(--success); margin-top:6px; flex-shrink:0;"></div>
                <div style="flex:1;">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Offer Extended to Elena Volkov</div>
                  <div style="font-size:11px; color:var(--text-secondary);">Director of Revenue Management pipeline</div>
                  <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">10 mins ago</div>
                </div>
              </div>
              <div style="display:flex; gap:12px;">
                <div style="width:8px; height:8px; border-radius:50%; background:var(--blue); margin-top:6px; flex-shrink:0;"></div>
                <div style="flex:1;">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Technical Interview Completed</div>
                  <div style="font-size:11px; color:var(--text-secondary);">Ayşe Kaya scored 4.8/5.0 in Rev strategy</div>
                  <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">1 hour ago</div>
                </div>
              </div>
              <div style="display:flex; gap:12px;">
                <div style="width:8px; height:8px; border-radius:50%; background:var(--purple); margin-top:6px; flex-shrink:0;"></div>
                <div style="flex:1;">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">CV Uploaded & Processed</div>
                  <div style="font-size:11px; color:var(--text-secondary);">Priya Sharma added to Director of Revenue</div>
                  <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">3 hours ago</div>
                </div>
              </div>
              <div style="display:flex; gap:12px;">
                <div style="width:8px; height:8px; border-radius:50%; background:var(--warning); margin-top:6px; flex-shrink:0;"></div>
                <div style="flex:1;">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">HR Interview Scheduled</div>
                  <div style="font-size:11px; color:var(--text-secondary);">HR Interview with Sophie Laurent set for Tomorrow</div>
                  <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">4 hours ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
"""
    
    html = before + dashboard_html + after
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard block patched successfully!")
else:
    print("Dashboard or Talent template tag not found!")
