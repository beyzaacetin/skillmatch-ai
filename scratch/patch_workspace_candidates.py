index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Start tag
start_tag = '<div v-if="workspaceTab === \'candidates\'">'
# End tag - start of upload tab:
end_tag = '<div v-if="workspaceTab === \'upload\'">'

start_idx = html.find(start_tag)
end_idx = html.find(end_tag)

if start_idx != -1 and end_idx != -1:
    before = html[:start_idx]
    after = html[end_idx:]
    
    candidates_tab_html = """<div v-if="workspaceTab === 'candidates'">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; background:var(--bg); padding:10px; border-radius:12px; border:1px solid var(--border);">
              <div style="display:flex; align-items:center; gap:8px;">
                <input type="checkbox" id="showPassiveToggle" v-model="showPassiveCandidates" style="width:14px; height:14px;">
                <label for="showPassiveToggle" style="font-weight:700; cursor:pointer; font-size:13px; color:var(--text-primary);">Show Passive / Rejected Candidates</label>
              </div>
              <button class="btn btn-primary btn-sm" @click="newCandidate.position_id = selectedPosition.id; showNewCandidateModal = true">+ Add Candidate</button>
            </div>

            <!-- Stage Collapsible Deck -->
            <div style="display:flex; flex-direction:column; gap:16px;">
              <div v-for="stg in [
                {value: 'offer', label: 'Offer', color: 'var(--success)'},
                {value: 'tech_interview', label: 'Technical Interview', color: 'var(--primary)'},
                {value: 'hr_interview', label: 'HR Interview', color: 'var(--purple)'},
                {value: 'screening', label: 'Screening', color: 'var(--warning)'},
                {value: 'applied', label: 'Applied', color: 'var(--blue)'}
              ]" :key="stg.value" class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); overflow:hidden; box-shadow:var(--sh);">
                
                <!-- Stage Header -->
                <div style="padding:16px 20px; background:var(--bg); border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; cursor:pointer;" @click="toggleStageCollapse(stg.value)">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <span :style="{transform: collapsedStages[stg.value] ? 'rotate(-90deg)' : 'rotate(0deg)'}" style="display:inline-block; font-size:12px; transition: transform 0.2s; color:var(--text-secondary);">▼</span>
                    <span style="font-weight:700; font-size:14px;" :style="{color: stg.color}">{{ stg.label }}</span>
                    <span class="badge" style="background:#FFF; border:1px solid var(--border); font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; color:var(--text-primary);">
                      {{ candidates.filter(c => c.position_id === selectedPosition.id && c.status === stg.value).length }}
                    </span>
                  </div>
                </div>
                
                <!-- Collapsible Body (Candidate Table) -->
                <div v-if="!collapsedStages[stg.value]" style="padding:12px 20px; overflow-x:auto;">
                  <table class="tbl" style="width:100%; border-collapse:collapse;" v-if="candidates.filter(c => c.position_id === selectedPosition.id && c.status === stg.value).length > 0">
                    <thead>
                      <tr style="background:var(--bg); border-bottom:1px solid var(--border);">
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Name</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Company</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; width:100px;">Match</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Status</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">HR Score</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Tech Score</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Final Score</th>
                        <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Last Activity</th>
                        <th style="padding:10px 12px; text-align:right; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; width:120px;">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="c in candidates.filter(c => c.position_id === selectedPosition.id && c.status === stg.value)" :key="c.id" style="cursor:pointer;" @click="openCandidateDrawer(c)" class="table-row">
                        <td style="padding:12px; border-bottom:1px solid var(--border); font-weight:700; color:var(--text-primary);">{{ c.name || c.full_name }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); color:var(--text-secondary);">{{ c.current_company || 'Apex Resorts' }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border);">
                          <div style="display:flex; align-items:center; gap:6px;">
                            <span style="font-weight:700; color:var(--primary); font-size:12px;">{{ Math.round(c.match_score || 80) }}%</span>
                          </div>
                        </td>
                        <td style="padding:12px; border-bottom:1px solid var(--border);"><span class="badge b-hired">ACTIVE</span></td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); font-weight:600;">{{ c.hr_interview_report?.overall_score ? c.hr_interview_report.overall_score + '%' : '—' }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); font-weight:600;">{{ c.technical_interview_report?.overall_score ? c.technical_interview_report.overall_score + '%' : '—' }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); font-weight:700; color:var(--primary);">{{ c.final_score > 0 ? c.final_score + '%' : '—' }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); color:var(--text-secondary); font-size:12px;">{{ formatDate(c.updated_at) || 'Today' }}</td>
                        <td style="padding:12px; border-bottom:1px solid var(--border); text-align:right;" @click.stop>
                          <div style="display:flex; gap:6px; justify-content:flex-end;">
                            <button class="btn btn-secondary btn-sm" style="padding:2px 8px; font-size:11px;" @click="openCandidateDrawer(c)">View</button>
                            <button class="btn btn-outline btn-sm" style="padding:2px 8px; font-size:11px;" @click="openCommunication(c, 'whatsapp')">WP</button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <div v-else style="text-align:center; padding:12px; color:var(--text-secondary); font-size:13px;">
                    No candidates in this stage.
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          """
    
    html = before + candidates_tab_html + after
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Candidates Tab block patched successfully!")
else:
    print("Candidates or Upload tab tag not found!")
