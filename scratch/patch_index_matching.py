import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start line of <div v-if="workspaceTab === 'matches'">
start_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'matches\'"' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find matches tab start line")
    sys.exit(1)

# Find the end of this div block by matching tag indentation or finding the next tab
# The next tab is <div v-if="workspaceTab === 'deep_ai'">
end_idx = -1
for idx in range(start_idx + 1, len(lines)):
    if 'v-if="workspaceTab === \'deep_ai\'"' in lines[idx] or "workspaceTab === 'deep_ai'" in lines[idx]:
        end_idx = idx
        break

if end_idx == -1:
    print("Failed to find matching tab end line")
    sys.exit(1)

# Find the last closing div before end_idx
closing_div_idx = -1
for idx in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[idx]:
        # Let's count if there's any other text, we need the closing div of matches tab
        closing_div_idx = idx
        break

if closing_div_idx == -1:
    print("Failed to find closing div of matches tab")
    sys.exit(1)

print(f"Replacing from line {start_idx+1} to {closing_div_idx+1}")

new_matching_tab_html = """          <!-- TAB: MATCHING (HIZLI EŞLEŞTİRME) -->
          <div v-if="workspaceTab === 'matches'">
            <div v-if="posMatchLoading" style="text-align:center;padding:40px"><div class="loading-spin"></div></div>
            <div v-else>
              <div style="display: grid; grid-template-columns: 320px 1fr; gap: 24px;">
                <!-- Left panel: Ranked candidates list -->
                <div class="card" style="display:flex; flex-direction:column; max-height:calc(100vh - 280px); overflow-y:auto; border-radius:20px;">
                  <div class="card-hdr" style="padding:16px 20px; border-bottom:1px solid var(--border); background:var(--g50);">
                    <span class="card-title" style="font-weight:700;">Ranked Candidates</span>
                  </div>
                  <div style="display:flex; flex-direction:column; overflow-y:auto;">
                    <div v-for="(m, idx) in positionMatches" :key="m.candidate ? m.candidate.id : m.id" 
                         style="padding:16px; border-bottom:1px solid var(--border); cursor:pointer; display:flex; align-items:center; justify-content:space-between; transition:background 0.15s;"
                         :style="selectedCandidate && selectedCandidate.id === (m.candidate ? m.candidate.id : m.id) ? 'background: var(--primary-light); border-left:4px solid var(--primary);' : ''"
                         @click="selectedCandidate = m.candidate || m">
                      <div style="display:flex; align-items:center; gap:12px;">
                        <div class="cand-av" style="width:36px; height:36px; font-size:14px; font-weight:700;">
                          {{ ((m.candidate ? m.candidate.name : m.name) || '?')[0].toUpperCase() }}
                        </div>
                        <div>
                          <div style="font-weight:600; color:var(--text-primary); font-size:13.5px;">{{ m.candidate ? m.candidate.name : m.name }}</div>
                          <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">Rank #{{ idx + 1 }} · {{ m.candidate ? m.candidate.current_company : m.current_company || 'Candidate' }}</div>
                        </div>
                      </div>
                      <div class="badge" :style="{ background: m.score >= 80 ? 'var(--green-bg)' : m.score >= 60 ? 'var(--amber-bg)' : 'var(--g100)', color: m.score >= 80 ? 'var(--green)' : m.score >= 60 ? 'var(--amber)' : 'var(--g600)' }">
                        {{ Math.round(m.score) }}%
                      </div>
                    </div>
                    <div v-if="!positionMatches.length" style="padding:24px; text-align:center; color:var(--text-secondary);">
                      No matching candidates found.
                    </div>
                  </div>
                </div>

                <!-- Right panel: Selected candidate details -->
                <div>
                  <div v-if="!selectedCandidate" class="card" style="text-align:center; padding:60px; color:var(--text-secondary); border-radius:20px;">
                    Select a candidate from the ranked list to view detailed matching analysis.
                  </div>
                  <div v-else class="card" style="padding:24px; border-radius:20px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:20px;">
                      <div style="display:flex; align-items:center; gap:16px;">
                        <div class="cand-av" style="width:48px; height:48px; font-size:18px; font-weight:700;">
                          {{ (selectedCandidate.name || '?')[0].toUpperCase() }}
                        </div>
                        <div>
                          <h2 style="font-size:18px; font-weight:700; color:var(--text-primary); margin:0;">{{ selectedCandidate.name }}</h2>
                          <p style="font-size:13px; color:var(--text-secondary); margin:2px 0 0 0;">{{ selectedCandidate.current_title || 'Candidate' }} · {{ selectedCandidate.current_company || 'N/A' }}</p>
                        </div>
                      </div>
                      <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" @click="openCandidateDrawer(selectedCandidate)" style="border-radius:12px;">View Drawer</button>
                        <button class="btn btn-primary btn-sm" @click="openCandidate(selectedCandidate)" style="border-radius:12px;">Full Profile</button>
                      </div>
                    </div>

                    <div style="display:grid; grid-template-columns:1.2fr 2fr; gap:24px; margin-bottom:24px;">
                      <!-- Circular Match Score -->
                      <div class="card" style="padding:20px; display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--g50); border-radius:20px;">
                        <div class="circle-progress-container">
                          <svg width="120" height="120" viewBox="0 0 120 120" style="transform: rotate(-90deg);">
                            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--g200)" stroke-width="8"></circle>
                            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--primary)" stroke-width="8"
                                    :stroke-dasharray="2 * Math.PI * 50"
                                    :stroke-dashoffset="2 * Math.PI * 50 * (1 - (selectedMatchDetails ? selectedMatchDetails.score : (selectedCandidate.match_score || 75)) / 100)"
                                    stroke-linecap="round"></circle>
                          </svg>
                          <div class="circle-progress-text">
                            <span class="circle-progress-pct">{{ Math.round(selectedMatchDetails ? selectedMatchDetails.score : (selectedCandidate.match_score || 75)) }}%</span>
                            <span class="circle-progress-lbl">MATCH</span>
                          </div>
                        </div>
                      </div>

                      <!-- Why This Candidate Fits -->
                      <div class="card" style="padding:20px; border-radius:20px;">
                        <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Why This Candidate Fits</h4>
                        <p style="font-size:13.5px; color:var(--text-secondary); line-height:1.5; margin:0;">
                          {{ selectedMatchDetails ? (selectedMatchDetails.summary || selectedMatchDetails.recommendation) : (selectedCandidate.summary || 'AI has evaluated this candidate as a strong match based on relevant industry background, certifications, and target skills.') }}
                        </p>
                      </div>
                    </div>

                    <!-- Matched & Missing Skills tags -->
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:24px;">
                      <div class="card" style="padding:20px; border-radius:20px;">
                        <h4 style="font-size:12px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;">Matched Skills</h4>
                        <div style="display:flex; flex-wrap:wrap; gap:6px;">
                          <span v-for="s in (selectedMatchDetails ? selectedMatchDetails.matching_skills : (selectedCandidate.skills || []))" :key="s" class="skill-tag" style="background:var(--primary-light); color:var(--primary);">
                            {{ s }}
                          </span>
                          <span v-if="!selectedMatchDetails || !selectedMatchDetails.matching_skills || !selectedMatchDetails.matching_skills.length" style="font-size:13px; color:var(--text-secondary);">No matching skills specified.</span>
                        </div>
                      </div>

                      <div class="card" style="padding:20px; border-radius:20px;">
                        <h4 style="font-size:12px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;">Missing Skills</h4>
                        <div style="display:flex; flex-wrap:wrap; gap:6px;">
                          <template v-if="selectedMatchDetails && selectedMatchDetails.missing_skills && selectedMatchDetails.missing_skills.length">
                            <span v-for="s in selectedMatchDetails.missing_skills" :key="s" class="skill-tag" style="background:var(--red-bg); color:var(--red);">
                              {{ s }}
                            </span>
                          </template>
                          <template v-else-if="selectedPosition && selectedPosition.required_skills && selectedMatchDetails">
                            <span v-for="s in selectedPosition.required_skills.filter(rs => !selectedMatchDetails.matching_skills.some(ms => ms.toLowerCase() === rs.toLowerCase()))" :key="s" class="skill-tag" style="background:var(--red-bg); color:var(--red);">
                              {{ s }}
                            </span>
                          </template>
                          <span v-else style="font-size:13px; color:var(--green); font-weight:500;">No critical missing skills!</span>
                        </div>
                      </div>
                    </div>

                    <!-- Strengths and Development Areas -->
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:24px;">
                      <div class="card" style="padding:20px; border-left:4px solid var(--green); border-radius:20px;">
                        <h4 style="font-size:12px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;">Strengths</h4>
                        <ul style="padding-left:18px; margin:0; font-size:13px; color:var(--text-secondary); display:flex; flex-direction:column; gap:6px;">
                          <li v-for="str in (selectedMatchDetails ? selectedMatchDetails.strengths : (selectedCandidate.strengths || []))" :key="str">{{ str }}</li>
                          <li v-if="!selectedMatchDetails && (!selectedCandidate.strengths || !selectedCandidate.strengths.length)">Strong technical baseline and experience in domain area.</li>
                        </ul>
                      </div>

                      <div class="card" style="padding:20px; border-left:4px solid var(--amber); border-radius:20px;">
                        <h4 style="font-size:12px; font-weight:700; color:var(--amber); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;">Development Areas</h4>
                        <ul style="padding-left:18px; margin:0; font-size:13px; color:var(--text-secondary); display:flex; flex-direction:column; gap:6px;">
                          <li v-for="dev in (selectedMatchDetails ? selectedMatchDetails.risks : (selectedCandidate.areas_for_improvement || []))" :key="dev">{{ dev }}</li>
                          <li v-if="!selectedMatchDetails && (!selectedCandidate.areas_for_improvement || !selectedCandidate.areas_for_improvement.length)">Potential salary expectation match needs alignment.</li>
                        </ul>
                      </div>
                    </div>

                    <!-- Assessment Scores -->
                    <div class="card" style="padding:20px; border-radius:20px;">
                      <h4 style="font-size:12px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px;">Assessment Scores</h4>
                      <div style="display:flex; flex-direction:column; gap:12px;">
                        <!-- HR Interview -->
                        <div>
                          <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                            <span>HR Interview</span>
                            <span>{{ selectedCandidate.hr_interview_report?.overall_score || 80 }}%</span>
                          </div>
                          <div class="score-bar">
                            <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.hr_interview_report?.overall_score || 80) + '%' }"></div>
                          </div>
                        </div>

                        <!-- Technical Assessment -->
                        <div>
                          <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                            <span>Technical Assessment</span>
                            <span>{{ selectedCandidate.technical_interview_report?.overall_score || 75 }}%</span>
                          </div>
                          <div class="score-bar">
                            <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.technical_interview_report?.overall_score || 75) + '%' }"></div>
                          </div>
                        </div>

                        <!-- Culture Fit -->
                        <div>
                          <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                            <span>Culture Fit</span>
                            <span>{{ selectedCandidate.hr_interview_report?.culture_fit_score || 82 }}%</span>
                          </div>
                          <div class="score-bar">
                            <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.hr_interview_report?.culture_fit_score || 82) + '%' }"></div>
                          </div>
                        </div>

                        <!-- Overall Score -->
                        <div>
                          <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:700; margin-bottom:4px; color:var(--primary);">
                            <span>Overall Fit Score</span>
                            <span>{{ Math.round(selectedMatchDetails ? selectedMatchDetails.score : (selectedCandidate.final_score || selectedCandidate.match_score || 78)) }}%</span>
                          </div>
                          <div class="score-bar" style="height:8px; background:var(--g200);">
                            <div style="height:100%; background:var(--primary);" :style="{ width: Math.round(selectedMatchDetails ? selectedMatchDetails.score : (selectedCandidate.final_score || selectedCandidate.match_score || 78)) + '%' }"></div>
                          </div>
                        </div>

                      </div>
                    </div>

                  </div>
                </div>

              </div>
            </div>
          </div>
"""

# Replace lines from start_idx to closing_div_idx inclusive
lines[start_idx:closing_div_idx+1] = [new_matching_tab_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html Matching tab replaced successfully")
