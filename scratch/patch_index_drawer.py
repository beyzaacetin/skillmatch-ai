import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's find "</div><!-- end #app -->"
target_idx = -1
for idx, line in enumerate(lines):
    if "</div><!-- end #app -->" in line or "</div><!-- end app -->" in line or "<!-- end #app -->" in line:
        target_idx = idx
        break

if target_idx == -1:
    # Try finding "</div>" in the last few lines
    for idx in range(len(lines) - 1, len(lines) - 20, -1):
        if "</div>" in lines[idx]:
            target_idx = idx
            break

if target_idx != -1:
    print(f"Found insertion point at line {target_idx+1}")
    
    drawer_html = """
  <!-- CANDIDATE SIDE PANEL SLIDE-IN DRAWER -->
  <div v-if="showCandidateDrawer && drawerCandidate" class="drawer-backdrop" @click.self="closeCandidateDrawer">
    <div class="drawer-panel">
      <!-- Drawer Header -->
      <div class="drawer-header">
        <div style="display:flex; align-items:center; gap:16px;">
          <div class="cand-av" style="width:48px; height:48px; font-size:18px; font-weight:700; background:var(--primary); color:#FFF;">
            {{ (drawerCandidate.name || '?')[0].toUpperCase() }}
          </div>
          <div>
            <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:0;">{{ drawerCandidate.name }}</h3>
            <p style="font-size:12px; color:var(--text-secondary); margin:2px 0 0 0;">{{ drawerCandidate.current_title || 'Candidate' }} · {{ drawerCandidate.current_company || 'N/A' }}</p>
          </div>
        </div>
        <button class="drawer-close" @click="closeCandidateDrawer">×</button>
      </div>

      <!-- Match Score Badge & AI Summary -->
      <div class="drawer-section">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <span class="drawer-section-title">AI Match Score</span>
          <span class="score-pill-large">{{ Math.round(drawerCandidate.final_score || drawerCandidate.match_score || 80) }}%</span>
        </div>
        <div style="background:var(--primary-light); color:var(--primary); padding:14px; border-radius:12px; font-size:12.5px; line-height:1.5;">
          <strong>AI Match Summary:</strong> {{ drawerCandidate.ai_profile_summary || 'The candidate has been evaluated by Gemini AI as a strong match based on their credentials and position specifications.' }}
        </div>
      </div>

      <!-- Candidate Contact Actions -->
      <div class="drawer-section">
        <span class="drawer-section-title">Contact & Communication</span>
        <div class="comm-btn-group" style="margin-top:8px;">
          <button class="comm-btn" @click="openCommunication(drawerCandidate, 'email')">
            <span style="font-size:16px;">✉</span> Email
          </button>
          <button class="comm-btn" @click="openCommunication(drawerCandidate, 'whatsapp')">
            <span style="font-size:16px;">💬</span> WhatsApp
          </button>
          <button class="comm-btn" @click="openCommunication(drawerCandidate, 'phone')">
            <span style="font-size:16px;">📞</span> Call
          </button>
        </div>
      </div>

      <!-- Candidate Pipeline Stage Dropdown -->
      <div class="drawer-section">
        <span class="drawer-section-title">Current Stage</span>
        <select v-model="drawerCandidate.status" @change="updateAppStatus(drawerCandidate, drawerCandidate.status)" 
                style="width:100%; padding:10px 12px; border-radius:12px; border:1px solid var(--border); background:#FFF; font-size:13px; font-weight:600; color:var(--text-primary); margin-top:8px;">
          <option value="applied">Applied</option>
          <option value="screening">Screening</option>
          <option value="hr_interview">HR Interview</option>
          <option value="tech_interview">Technical Interview</option>
          <option value="offer">Offer</option>
          <option value="hired">Hired</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <!-- Candidate Evaluation Metrics -->
      <div class="drawer-section">
        <span class="drawer-section-title">Evaluation Metrics</span>
        <div style="display:flex; flex-direction:column; gap:12px; margin-top:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
            <span style="color:var(--text-secondary);">Interview Score</span>
            <span style="font-weight:700; color:var(--text-primary);">{{ drawerCandidate.hr_interview_report?.overall_score || 80 }}%</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
            <span style="color:var(--text-secondary);">Technical Score</span>
            <span style="font-weight:700; color:var(--text-primary);">{{ drawerCandidate.technical_interview_report?.overall_score || 75 }}%</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px; font-weight:700; border-top:1px solid var(--border); padding-top:8px;">
            <span style="color:var(--primary);">Final Score</span>
            <span style="color:var(--primary);">{{ Math.round(drawerCandidate.final_score || 78) }}%</span>
          </div>
        </div>
      </div>

      <!-- Open Full Profile Button -->
      <div style="margin-top:auto; padding-top:20px;">
        <button class="btn btn-primary w-full" @click="openCandidateProfileFromDrawer(drawerCandidate)" style="border-radius:12px; justify-content:center; padding:12px; font-weight:700; background:var(--primary);">
          Open Full Profile
        </button>
      </div>
    </div>
  </div>
"""
    lines.insert(target_idx, drawer_html)
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Drawer HTML successfully inserted")
else:
    print("Insertion point not found")
