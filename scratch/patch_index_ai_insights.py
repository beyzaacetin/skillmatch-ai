import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'deep_ai\'"' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find deep_ai tab start line")
    sys.exit(1)

# Find ending line
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if 'v-if="workspaceTab === \'hr_interview\'"' in lines[i] or 'workspaceTab === \'hr_interview\'' in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Failed to find deep_ai ending line")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of deep_ai tab")
    sys.exit(1)

print(f"Replacing deep_ai tab from line {start_idx+1} to {closing_div_idx+1}")

new_deep_ai_html = """          <!-- TAB: AI INSIGHTS (AI KRİTER ANALİZİ) -->
          <div v-if="workspaceTab === 'deep_ai'">
            <div v-if="workspaceAiInsightsLoading" style="text-align:center;padding:40px"><div class="loading-spin"></div></div>
            <div v-else-if="workspaceAiInsights">
              <!-- KPI Cards Strip -->
              <div class="grid-4" style="margin-bottom:24px; gap:20px;">
                <div class="stat-card" style="padding:16px; border-radius:16px; background:#FFF; border:1px solid var(--border);">
                  <div style="font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Estimated Time To Fill</div>
                  <div style="font-size:24px; font-weight:800; color:var(--text-primary);">{{ workspaceAiInsights.estimated_time_to_fill }}</div>
                </div>
                <div class="stat-card" style="padding:16px; border-radius:16px; background:#FFF; border:1px solid var(--border);">
                  <div style="font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Pipeline Quality Score</div>
                  <div style="font-size:24px; font-weight:800; color:var(--text-primary);">{{ workspaceAiInsights.pipeline_quality_score }}</div>
                </div>
                <div class="stat-card" style="padding:16px; border-radius:16px; background:#FFF; border:1px solid var(--border);">
                  <div style="font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Interview To Offer Conversion</div>
                  <div style="font-size:24px; font-weight:800; color:var(--text-primary);">{{ workspaceAiInsights.interview_to_offer_conversion }}</div>
                </div>
                <div class="stat-card" style="padding:16px; border-radius:16px; background:#FFF; border:1px solid var(--border);">
                  <div style="font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Estimated Cost-to-Hire</div>
                  <div style="font-size:24px; font-weight:800; color:var(--text-primary);">{{ workspaceAiInsights.estimated_cost_to_hire }}</div>
                </div>
              </div>

              <!-- Main Split Area -->
              <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px;">
                <!-- Left panel: Recommended & Risks -->
                <div style="display:flex; flex-direction:column; gap:24px;">
                  <!-- Top Recommended Candidates -->
                  <div class="card" style="border-radius:20px; padding:20px;">
                    <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px; display:flex; align-items:center; gap:6px;">
                      <span>★</span> Top Recommended Candidates
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                      <div v-for="c in candidates.filter(cand => cand.position_id === selectedPosition.id).slice(0, 3)" :key="c.id" 
                           style="display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border:1px solid var(--border); border-radius:12px; background:var(--g50);">
                        <div style="display:flex; align-items:center; gap:12px;">
                          <div class="cand-av" style="width:36px; height:36px; font-size:14px; font-weight:700; background:var(--primary); color:#FFF;">
                            {{ (c.name || '?')[0].toUpperCase() }}
                          </div>
                          <div>
                            <div style="font-weight:600; color:var(--text-primary); font-size:13.5px;">{{ c.name }}</div>
                            <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">{{ c.current_title || 'Candidate' }} · {{ c.current_company || 'N/A' }}</div>
                          </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:12px;">
                          <div style="text-align:right;">
                            <div style="font-size:16px; font-weight:800; color:var(--primary);">{{ Math.round(c.final_score || c.match_score || 80) }}%</div>
                            <div style="font-size:9px; color:var(--text-secondary);">MATCH</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Position Risks -->
                  <div class="card" style="border-radius:20px; padding:20px;">
                    <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px; display:flex; align-items:center; gap:6px;">
                      <span>⚠</span> Position Risks
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                      <div v-for="risk in workspaceAiInsights.risks" :key="risk.title" 
                           style="padding:14px; border-radius:12px; border-left:4px solid var(--amber); background:#FFFBEB;">
                        <div style="font-weight:700; font-size:13px; color:#B45309;">{{ risk.title }}</div>
                        <div style="font-size:12px; color:#78350F; margin-top:4px; line-height:1.5;">{{ risk.description }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Right panel: Velocity & Interview Questions -->
                <div style="display:flex; flex-direction:column; gap:24px;">
                  <!-- Pipeline Velocity -->
                  <div class="card" style="border-radius:20px; padding:20px;">
                    <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px; display:flex; align-items:center; gap:6px;">
                      <span>📊</span> Pipeline Velocity
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:16px;">
                      <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
                          <span>Applied → Screening</span>
                          <span style="color:var(--text-secondary);">4.2d / 3d avg</span>
                        </div>
                        <div class="score-bar" style="height:8px; background:var(--g200); border-radius:4px;">
                          <div style="height:100%; background:var(--primary); width:75%;"></div>
                        </div>
                      </div>
                      <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
                          <span>Screening → HR Interview</span>
                          <span style="color:var(--text-secondary);">6.8d / 5d avg</span>
                        </div>
                        <div class="score-bar" style="height:8px; background:var(--g200); border-radius:4px;">
                          <div style="height:100%; background:var(--red); width:90%;"></div>
                        </div>
                      </div>
                      <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
                          <span>HR Interview → Technical</span>
                          <span style="color:var(--text-secondary);">2.1d / 3d avg</span>
                        </div>
                        <div class="score-bar" style="height:8px; background:var(--g200); border-radius:4px;">
                          <div style="height:100%; background:var(--green); width:40%;"></div>
                        </div>
                      </div>
                      <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
                          <span>Technical → Offer</span>
                          <span style="color:var(--text-secondary);">3.4d / 5d avg</span>
                        </div>
                        <div class="score-bar" style="height:8px; background:var(--g200); border-radius:4px;">
                          <div style="height:100%; background:var(--green); width:60%;"></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- AI-Suggested Interview Questions -->
                  <div class="card" style="border-radius:20px; padding:20px;">
                    <h4 style="font-size:13px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:16px; display:flex; align-items:center; gap:6px;">
                      <span>💬</span> Suggested Interview Questions
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                      <div v-for="(q, index) in workspaceAiInsights.suggested_questions" :key="index" 
                           style="padding:12px; border-radius:12px; background:var(--g50); border:1px solid var(--border); display:flex; gap:10px; align-items:flex-start;">
                        <div style="width:20px; height:20px; border-radius:50%; background:var(--primary); color:#FFF; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; flex-shrink:0; margin-top:2px;">
                          {{ index + 1 }}
                        </div>
                        <div style="font-size:12.5px; color:var(--text-primary); line-height:1.5;">{{ q }}</div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
            <div v-else class="empty" style="padding:40px; text-align:center;">
              <button class="btn btn-primary" @click="loadPositionAiInsights(selectedPosition.id)" style="border-radius:12px;">Generate AI Insights</button>
            </div>
          </div>
"""

lines[start_idx:closing_div_idx+1] = [new_deep_ai_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html AI Insights tab replaced successfully")
