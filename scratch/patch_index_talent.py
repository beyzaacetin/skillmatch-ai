index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Start tag
start_tag = '<template v-if="page===' + "'talent'" + '">'
# End of list view / table card:
end_tag = '<!-- GRID VIEW -->'

start_idx = html.find(start_tag)
end_idx = html.find(end_tag)

if start_idx != -1 and end_idx != -1:
    before = html[:start_idx]
    after = html[end_idx:]
    
    talent_html = """<template v-if="page==='talent'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Candidates</div>
          <div class="page-hdr-sub">Manage your talent pool and application pipeline</div>
        </div>
        <div style="margin-left:auto; display:flex; gap:12px; align-items:center;">
          <div class="search-bar" style="height:36px; display:flex; align-items:center; gap:8px; background:var(--g100); border-radius:12px; padding:0 12px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="candidateSearch" placeholder="Search candidates, positions..." style="border:none; background:transparent; outline:none; font-size:12.5px; width:100%;">
          </div>
          <button class="btn btn-secondary btn-sm" style="height:36px; border-radius:12px;" @click="alert('Filters: Seniority, stage, and sorting options.')">Filter</button>
          <button class="btn btn-primary btn-sm" style="height:36px; border-radius:12px;" @click="newCandidate = {position_id: ''}; showNewCandidateModal=true;">Add Candidate</button>
        </div>
      </div>

      <div class="page-body">
        <!-- Top KPI Cards -->
        <div style="margin-bottom:24px; display:grid; grid-template-columns:repeat(4, 1fr); gap:16px;">
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Total Candidates</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ candidates.length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Active Pipeline</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ candidates.filter(c => c.status !== 'hired' && c.status !== 'rejected').length }}</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Avg Match Score</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">82.5%</div>
          </div>
          <div class="stat-card" style="padding:16px; border-radius:12px; background:#FFF; border:1px solid var(--border); box-shadow:var(--sh);">
            <div style="font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Offers Outstanding</div>
            <div style="font-size:24px; font-weight:700; color:var(--text-primary);">{{ candidates.filter(c => c.status === 'offer').length }}</div>
          </div>
        </div>

        <!-- Filter bar -->
        <div style="display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; align-items:center;">
          <select v-model="talentFilter.seniority" class="fs" style="width:auto; padding:6px 12px; font-size:12.5px; border-radius:8px;">
            <option value="">All Seniorities</option>
            <option>Junior</option><option>Mid</option><option>Senior</option>
          </select>
          <select v-model="talentFilter.sort" class="fs" style="width:auto; padding:6px 12px; font-size:12.5px; border-radius:8px;">
            <option value="newest">Newest</option>
            <option value="name">Name A-Z</option>
            <option value="rating">Highest Rating</option>
            <option value="score">Highest Match Score</option>
          </select>
          <label style="display:flex; align-items:center; gap:6px; font-size:12px; color:var(--text-secondary); cursor:pointer;">
            <input type="checkbox" v-model="talentFilter.showInactive" style="width:14px; height:14px;">
            Show Passive / Blacklisted
          </label>
        </div>

        <!-- LIST VIEW: Candidates Table -->
        <div class="card" style="overflow:hidden; border-radius:16px; box-shadow:var(--sh);">
          <table class="tbl" style="width:100%; border-collapse:collapse;">
            <thead>
              <tr style="background:var(--bg);">
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Candidate</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Position Applied</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Stage</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; width:150px;">Match</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Status</th>
                <th style="padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Last Activity</th>
                <th style="padding:12px 16px; text-align:right; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; width:120px;">Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in filteredCandidates" :key="c.id" @click="openCandidate(c)" style="cursor:pointer; transition: background 0.15s;" class="table-row">
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:12px;">
                    <div class="cand-av" style="width:36px; height:36px; border-radius:50%; background:var(--primary-light); color:var(--primary); font-weight:700; display:flex; align-items:center; justify-content:center;">
                      {{ (c.name || 'C').split(' ').map(n=>n[0]).join('') }}
                    </div>
                    <div>
                      <div style="font-weight:700; color:var(--text-primary); font-size:13.5px;">{{ c.name }}</div>
                      <div style="font-size:12px; color:var(--text-secondary);">{{ c.seniority_level || 'Software Engineer' }} • {{ c.source || 'Direct' }}</div>
                    </div>
                  </div>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-primary);">
                  {{ c.best_position?.title || 'Director of Revenue Management' }}
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <span class="badge" :class="'b-' + c.status">{{ c.status.replace('_', ' ').toUpperCase() }}</span>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:8px;">
                    <div style="flex:1; height:6px; background:#E5E7EB; border-radius:3px; overflow:hidden;">
                      <div :style="{width: (c.match_score || 80) + '%'}" style="height:100%; background:var(--primary); border-radius:3px;"></div>
                    </div>
                    <span style="font-size:12px; font-weight:700; color:var(--primary);">{{ Math.round(c.match_score || 80) }}%</span>
                  </div>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border);">
                  <span v-if="c.is_blacklisted" class="badge b-rejected" style="font-weight:700;">BLACKLISTED</span>
                  <span v-else class="badge b-hired" style="font-weight:700;">ACTIVE</span>
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); color:var(--text-secondary); font-size:13px;">
                  {{ formatDate(c.updated_at) || 'Today' }}
                </td>
                <td style="padding:14px 16px; border-bottom:1px solid var(--border); text-align:right;" @click.stop>
                  <div class="stars" style="display:inline-flex; gap:2px; justify-content:flex-end;">
                    <svg v-for="i in 5" :key="i" class="star" :class="{on: i <= (c.rating || 4)}" viewBox="0 0 24 24" fill="currentColor" style="width:14px; height:14px; color:#D1D5DB; cursor:pointer;" @click="rateCandidate(c, i)">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
"""
    
    html = before + talent_html + after
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Candidates List page patched successfully!")
else:
    print("Talent start or Grid view tag not found!")
