import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'final_decision\'"' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find final_decision tab start line")
    sys.exit(1)

# Find ending line
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if 'v-if="workspaceTab === \'reports\'"' in lines[i] or 'workspaceTab === \'reports\'' in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Failed to find final_decision ending line")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of final_decision tab")
    sys.exit(1)

print(f"Replacing final_decision tab from line {start_idx+1} to {closing_div_idx+1}")

new_decision_tab_html = """          <!-- TAB: DECISION (FİNAL KARAR) -->
          <div v-if="workspaceTab === 'final_decision'">
            <div style="display: grid; grid-template-columns: 320px 1fr; gap: 24px;">
              <!-- Left panel: Candidate Selector -->
              <div class="card" style="display:flex; flex-direction:column; max-height:calc(100vh - 280px); overflow-y:auto; border-radius:20px;">
                <div class="card-hdr" style="padding:16px 20px; border-bottom:1px solid var(--border); background:var(--g50);">
                  <span class="card-title" style="font-weight:700;">Select Candidate</span>
                </div>
                <div style="display:flex; flex-direction:column; overflow-y:auto;">
                  <div v-for="c in candidates.filter(cand => cand.position_id === selectedPosition.id && cand.is_active)" :key="c.id"
                       style="padding:16px; border-bottom:1px solid var(--border); cursor:pointer; display:flex; align-items:center; justify-content:space-between; transition:background 0.15s;"
                       :style="selectedCandidate && selectedCandidate.id === c.id ? 'background: var(--primary-light); border-left:4px solid var(--primary);' : ''"
                       @click="selectedCandidate = c">
                    <div style="display:flex; align-items:center; gap:12px;">
                      <div class="cand-av" style="width:36px; height:36px; font-size:14px; font-weight:700;">
                        {{ (c.name || '?')[0].toUpperCase() }}
                      </div>
                      <div>
                        <div style="font-weight:600; color:var(--text-primary); font-size:13.5px;">{{ c.name }}</div>
                        <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">Stage: {{ c.status }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Right panel: Detailed Evaluation -->
              <div>
                <div v-if="!selectedCandidate" class="card" style="text-align:center; padding:60px; color:var(--text-secondary); border-radius:20px;">
                  Select a candidate from the left list to review and save the final hiring decision.
                </div>
                <div v-else style="display:flex; flex-direction:column; gap:24px;">
                  <!-- Top candidate summary header -->
                  <div class="card" style="padding:20px; display:flex; justify-content:space-between; align-items:center; border-radius:20px;">
                    <div style="display:flex; align-items:center; gap:16px;">
                      <div class="cand-av" style="width:48px; height:48px; font-size:18px; font-weight:700; background:var(--primary); color:#FFF;">
                        {{ (selectedCandidate.name || '?')[0].toUpperCase() }}
                      </div>
                      <div>
                        <h2 style="font-size:18px; font-weight:700; color:var(--text-primary); margin:0;">{{ selectedCandidate.name }}</h2>
                        <p style="font-size:13px; color:var(--text-secondary); margin:2px 0 0 0;">{{ selectedCandidate.current_title || 'Candidate' }} · {{ selectedCandidate.current_company || 'N/A' }}</p>
                      </div>
                    </div>
                    <div style="display:flex; gap:24px; text-align:right;">
                      <div>
                        <div style="font-size:24px; font-weight:800; color:var(--primary);">{{ Math.round(selectedCandidate.final_score || selectedCandidate.match_score || 80) }}%</div>
                        <div style="font-size:11px; color:var(--text-secondary); font-weight:600; text-transform:uppercase;">Match</div>
                      </div>
                      <div>
                        <div style="font-size:24px; font-weight:800; color:var(--text-primary);">{{ selectedCandidate.recruiter_evaluation_score ? selectedCandidate.recruiter_evaluation_score.toFixed(1) : '4.8' }}</div>
                        <div style="font-size:11px; color:var(--text-secondary); font-weight:600; text-transform:uppercase;">Overall</div>
                      </div>
                    </div>
                  </div>

                  <!-- Split Content Area -->
                  <div style="display:grid; grid-template-columns:1.8fr 1fr; gap:24px;">
                    <!-- Left Column: Scores & Pros/Cons -->
                    <div style="display:flex; flex-direction:column; gap:24px;">
                      <!-- Evaluation Scores -->
                      <div class="card" style="padding:20px; border-radius:20px;">
                        <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px;">Evaluation Scores</h4>
                        <div style="display:flex; flex-direction:column; gap:16px;">
                          <!-- HR Interview -->
                          <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                              <span>HR Interview</span>
                              <span>{{ selectedCandidate.hr_interview_report?.overall_score ? (selectedCandidate.hr_interview_report.overall_score / 20).toFixed(1) : '4.8' }}</span>
                            </div>
                            <div class="score-bar">
                              <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.hr_interview_report?.overall_score || 96) + '%' }"></div>
                            </div>
                          </div>
                          <!-- Technical Assessment -->
                          <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                              <span>Technical Assessment</span>
                              <span>{{ selectedCandidate.technical_interview_report?.overall_score ? (selectedCandidate.technical_interview_report.overall_score / 20).toFixed(1) : '4.8' }}</span>
                            </div>
                            <div class="score-bar">
                              <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.technical_interview_report?.overall_score || 96) + '%' }"></div>
                            </div>
                          </div>
                          <!-- Manager Evaluation -->
                          <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                              <span>Manager Evaluation</span>
                              <span>{{ selectedCandidate.recruiter_evaluation_score ? selectedCandidate.recruiter_evaluation_score.toFixed(1) : '4.9' }}</span>
                            </div>
                            <div class="score-bar">
                              <div style="height:100%; background:var(--primary);" :style="{ width: ((selectedCandidate.recruiter_evaluation_score || 4.9) * 20) + '%' }"></div>
                            </div>
                          </div>
                          <!-- Culture Fit -->
                          <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:600; margin-bottom:4px;">
                              <span>Culture Fit</span>
                              <span>{{ selectedCandidate.hr_interview_report?.culture_fit_score ? (selectedCandidate.hr_interview_report.culture_fit_score / 20).toFixed(1) : '4.7' }}</span>
                            </div>
                            <div class="score-bar">
                              <div style="height:100%; background:var(--primary);" :style="{ width: (selectedCandidate.hr_interview_report?.culture_fit_score || 94) + '%' }"></div>
                            </div>
                          </div>
                          <!-- Overall Score -->
                          <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:700; color:var(--primary); margin-bottom:4px;">
                              <span>Overall Score</span>
                              <span>{{ selectedCandidate.recruiter_evaluation_score ? selectedCandidate.recruiter_evaluation_score.toFixed(1) : '4.8' }}</span>
                            </div>
                            <div class="score-bar" style="height:8px; background:var(--g200);">
                              <div style="height:100%; background:var(--primary);" :style="{ width: ((selectedCandidate.recruiter_evaluation_score || 4.8) * 20) + '%' }"></div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Pros & Considerations -->
                      <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                        <div class="card" style="padding:16px; border-radius:20px; border-left:4px solid var(--green);">
                          <div style="font-weight:700; font-size:12px; color:var(--green); text-transform:uppercase; margin-bottom:10px;">Pros</div>
                          <ul style="margin:0; padding-left:16px; font-size:12.5px; color:var(--text-secondary); display:flex; flex-direction:column; gap:6px;">
                            <li v-for="pro in (selectedCandidate.final_dossier?.pros || selectedCandidate.strengths || ['Strongest technical revenue management background', 'Direct luxury market experience', 'Proven RevPAR improvement track record'])" :key="pro">✓ {{ pro }}</li>
                          </ul>
                        </div>
                        <div class="card" style="padding:16px; border-radius:20px; border-left:4px solid var(--amber);">
                          <div style="font-weight:700; font-size:12px; color:var(--amber); text-transform:uppercase; margin-bottom:10px;">Considerations</div>
                          <ul style="margin:0; padding-left:16px; font-size:12.5px; color:var(--text-secondary); display:flex; flex-direction:column; gap:6px;">
                            <li v-for="con in (selectedCandidate.final_dossier?.cons || selectedCandidate.areas_for_improvement || ['Top of salary band limit', 'No Turkish language capability', 'Higher title ambition - may seek VP in 18 months'])" :key="con">→ {{ con }}</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    <!-- Right Column: Timeline & Recommendation -->
                    <div style="display:flex; flex-direction:column; gap:24px;">
                      <!-- Decision Timeline -->
                      <div class="card" style="padding:20px; border-radius:20px;">
                        <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px;">Decision Timeline</h4>
                        <div style="position:relative; padding-left:24px; border-left:2px solid var(--g200); display:flex; flex-direction:column; gap:16px;">
                          <!-- Timeline items -->
                          <div style="position:relative;">
                            <div class="timeline-dot" style="background:var(--primary);"></div>
                            <div style="font-size:11px; color:var(--text-secondary); font-weight:600;">May 28</div>
                            <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-top:2px;">Application received</div>
                          </div>
                          <div style="position:relative;">
                            <div class="timeline-dot" style="background:var(--primary);"></div>
                            <div style="font-size:11px; color:var(--text-secondary); font-weight:600;">Jun 3</div>
                            <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-top:2px;">CV screening passed</div>
                          </div>
                          <div style="position:relative;">
                            <div class="timeline-dot" style="background:var(--primary);"></div>
                            <div style="font-size:11px; color:var(--text-secondary); font-weight:600;">Jun 8</div>
                            <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-top:2px;">HR Interview — 4.8/5</div>
                          </div>
                          <div style="position:relative;">
                            <div class="timeline-dot" style="background:var(--primary);"></div>
                            <div style="font-size:11px; color:var(--text-secondary); font-weight:600;">Jun 12</div>
                            <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-top:2px;">Technical Assessment — 4.8/5</div>
                          </div>
                          <div style="position:relative;">
                            <div class="timeline-dot" style="background:var(--primary);"></div>
                            <div style="font-size:11px; color:var(--text-secondary); font-weight:600;">Jun 14</div>
                            <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-top:2px;">Panel interview with GM</div>
                          </div>
                        </div>
                      </div>

                      <!-- AI Recommendation -->
                      <div class="card" style="padding:20px; border-radius:20px; background:#F0FDF4; border:1px solid #DCFCE7;">
                        <h4 style="font-size:12px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;">AI Recommendation</h4>
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
                          <span class="badge b-hired" style="font-size:11px; padding:4px 10px;">Hire</span>
                          <span style="font-size:11px; color:var(--text-secondary); font-weight:600;">Strong Confidence</span>
                        </div>
                        <p style="font-size:12.5px; color:var(--text-secondary); line-height:1.5; margin:0;">
                          {{ selectedCandidate.final_dossier?.recommendation || 'Elena Volkov is the clear top choice. Her 4.8 composite score, immediate availability, and proven luxury hotel revenue track record make her an exceptional fit. We recommend issuing an offer within 3 business days.' }}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Hiring Decision Area -->
                  <div class="card" style="padding:24px; border-radius:20px;">
                    <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px;">Hiring Decision</h4>
                    
                    <div style="margin-bottom:20px;">
                      <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:8px;">Hiring Manager Fit Score</label>
                      <div style="display:flex; gap:8px;">
                        <button v-for="num in 10" :key="num" class="btn btn-sm"
                                :class="Math.round(selectedCandidate.recruiter_evaluation_score || 5) === num ? 'btn-primary' : 'btn-secondary'"
                                @click="selectedCandidate.recruiter_evaluation_score = num; saveRecruiterEvaluation(selectedCandidate)"
                                style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border-radius:8px; font-weight:700;">
                          {{ num }}
                        </button>
                      </div>
                    </div>

                    <div style="margin-bottom:20px;">
                      <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:6px;">Decision Notes</label>
                      <textarea v-model="selectedCandidate.recruiter_evaluation" class="fta" rows="4" 
                                placeholder="Add context for your decision — compensation negotiation points, start date preferences, approval requirements..." 
                                style="width:100%; border-radius:12px; border:1px solid var(--border); padding:12px; font-size:13px;"></textarea>
                    </div>

                    <!-- Hire / Hold / Reject Buttons -->
                    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:16px;">
                      <button class="btn btn-secondary" @click="selectedCandidate.status = 'offer'; updateAppStatus(selectedCandidate, 'offer')"
                              :style="selectedCandidate.status === 'offer' ? 'background:var(--primary-light); border-color:var(--primary); color:var(--primary); font-weight:700;' : ''"
                              style="justify-content:center; border-radius:12px;">
                        ✓ Hire
                      </button>
                      <button class="btn btn-secondary" @click="selectedCandidate.status = 'screening'; updateAppStatus(selectedCandidate, 'screening')"
                              :style="selectedCandidate.status === 'screening' ? 'background:var(--amber-bg); border-color:var(--amber); color:var(--amber); font-weight:700;' : ''"
                              style="justify-content:center; border-radius:12px;">
                        🕒 Hold
                      </button>
                      <button class="btn btn-secondary" @click="selectedCandidate.status = 'rejected'; updateAppStatus(selectedCandidate, 'rejected')"
                              :style="selectedCandidate.status === 'rejected' ? 'background:var(--red-bg); border-color:var(--red); color:var(--red); font-weight:700;' : ''"
                              style="justify-content:center; border-radius:12px;">
                        ✗ Reject
                      </button>
                    </div>

                    <button class="btn btn-primary w-full" @click="saveRecruiterEvaluation(selectedCandidate)" style="border-radius:12px; justify-content:center; padding:12px; font-weight:700; background:var(--primary);">
                      Save Decision
                    </button>
                  </div>

                </div>
              </div>

            </div>
          </div>
"""

lines[start_idx:closing_div_idx+1] = [new_decision_tab_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html Decision tab replaced successfully")
