import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'reports\'"' in line:
        start_idx = idx
        break

if start_idx == -1:
    print("Failed to find reports tab start line")
    sys.exit(1)

# Find ending line
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if 'v-if="workspaceTab === \'calendar\'"' in lines[i] or 'workspaceTab === \'calendar\'' in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Failed to find reports ending line")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of reports tab")
    sys.exit(1)

print(f"Replacing reports tab from line {start_idx+1} to {closing_div_idx+1}")

new_reports_tab_html = """          <!-- TAB: REPORTS (RAPORLAR & PDF UPLOAD) -->
          <div v-if="workspaceTab === 'reports'">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
              <div>
                <h2 style="font-size:18px; font-weight:700; color:var(--text-primary); margin:0;">Report Center</h2>
                <p style="font-size:13px; color:var(--text-secondary); margin:4px 0 0 0;">{{ selectedPosition.title }} — {{ selectedPosition.department }}</p>
              </div>
              <button class="btn btn-primary btn-sm" @click="alert('Downloading all reports...')" style="border-radius:12px; background:var(--primary); height:38px; display:inline-flex; align-items:center; gap:6px;">
                <span>📥</span> Download All Reports
              </button>
            </div>

            <!-- Grid of 4 Report Cards -->
            <div class="grid-2" style="gap:24px; margin-bottom:24px;">
              <!-- HR Evaluation Report -->
              <div class="card" style="padding:24px; border-radius:20px; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; position:relative;">
                <span class="badge b-hired" style="position:absolute; top:24px; right:24px; font-size:10px;">Ready</span>
                <div>
                  <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; font-size:18px;">👥</div>
                    <h3 style="font-size:15px; font-weight:700; color:var(--text-primary); margin:0;">HR Evaluation Report</h3>
                  </div>
                  <p style="font-size:12.5px; color:var(--text-secondary); line-height:1.5; margin-bottom:12px;">
                    Comprehensive HR interview assessment including competency evaluation, cultural fit analysis, and behavioral indicators for all shortlisted candidates.
                  </p>
                  <p style="font-size:11px; color:var(--text-secondary); font-weight:600; margin-bottom:16px;">
                    5 candidates · 12 pages · Jun 14, 2024
                  </p>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-secondary btn-sm" style="border-radius:12px;" @click="alert('Previewing HR Evaluation Report...')">👁 Preview</button>
                  <button class="btn btn-primary btn-sm" style="border-radius:12px;" @click="selectedCandidate ? generateHrReport(selectedCandidate) : alert('Select a candidate in Decision tab first to generate detailed reports.')">📥 Download PDF</button>
                </div>
              </div>

              <!-- Technical Evaluation Report -->
              <div class="card" style="padding:24px; border-radius:20px; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; position:relative;">
                <span class="badge b-hired" style="position:absolute; top:24px; right:24px; font-size:10px;">Ready</span>
                <div>
                  <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; font-size:18px;">📊</div>
                    <h3 style="font-size:15px; font-weight:700; color:var(--text-primary); margin:0;">Technical Evaluation Report</h3>
                  </div>
                  <p style="font-size:12.5px; color:var(--text-secondary); line-height:1.5; margin-bottom:12px;">
                    Detailed technical competency assessment covering revenue management systems, analytical skills, and domain knowledge scores.
                  </p>
                  <p style="font-size:11px; color:var(--text-secondary); font-weight:600; margin-bottom:16px;">
                    3 candidates · 8 pages · Jun 12, 2024
                  </p>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-secondary btn-sm" style="border-radius:12px;" @click="alert('Previewing Technical Evaluation Report...')">👁 Preview</button>
                  <button class="btn btn-primary btn-sm" style="border-radius:12px;" @click="selectedCandidate ? generateTechReport(selectedCandidate) : alert('Select a candidate in Decision tab first to generate detailed reports.')">📥 Download PDF</button>
                </div>
              </div>

              <!-- Candidate Summary Report -->
              <div class="card" style="padding:24px; border-radius:20px; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; position:relative;">
                <span class="badge b-hired" style="position:absolute; top:24px; right:24px; font-size:10px;">Ready</span>
                <div>
                  <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; font-size:18px;">📄</div>
                    <h3 style="font-size:15px; font-weight:700; color:var(--text-primary); margin:0;">Candidate Summary Report</h3>
                  </div>
                  <p style="font-size:12.5px; color:var(--text-secondary); line-height:1.5; margin-bottom:12px;">
                    Executive overview summaries for all active candidates, includes match scores, stage history, and key highlights for hiring committee review.
                  </p>
                  <p style="font-size:11px; color:var(--text-secondary); font-weight:600; margin-bottom:16px;">
                    5 candidates · 10 pages · Jun 14, 2024
                  </p>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-secondary btn-sm" style="border-radius:12px;" @click="alert('Previewing Candidate Summary Report...')">👁 Preview</button>
                  <button class="btn btn-primary btn-sm" style="border-radius:12px;" @click="selectedCandidate ? generateFinalDossier(selectedCandidate) : alert('Select a candidate in Decision tab first to generate detailed reports.')">📥 Download PDF</button>
                </div>
              </div>

              <!-- Final Hiring Report -->
              <div class="card" style="padding:24px; border-radius:20px; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; position:relative;">
                <span class="badge b-screening" style="position:absolute; top:24px; right:24px; font-size:10px;">Pending</span>
                <div>
                  <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; font-size:18px;">🤝</div>
                    <h3 style="font-size:15px; font-weight:700; color:var(--text-primary); margin:0;">Final Hiring Report</h3>
                  </div>
                  <p style="font-size:12.5px; color:var(--text-secondary); line-height:1.5; margin-bottom:12px;">
                    Complete hiring package for the recommended candidate including offer justification, compensation benchmarking, and onboarding recommendations.
                  </p>
                  <p style="font-size:11px; color:var(--text-secondary); font-weight:600; margin-bottom:16px;">
                    1 candidate
                  </p>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-primary btn-sm" style="border-radius:12px; width:100%; justify-content:center; background:var(--primary);" @click="selectedCandidate ? generateFinalDossier(selectedCandidate) : alert('Select a candidate in Decision tab first to generate reports.')">Generate Report</button>
                </div>
              </div>
            </div>

            <!-- Disclaimer Banner -->
            <div style="background:#FFF; border:1px solid var(--border); border-radius:12px; padding:16px; font-size:12px; color:var(--text-secondary); line-height:1.5;">
              All reports are generated in PDF format with full Unicode support, including Turkish characters (ı, ş, ğ, ö, ç, ü). Reports are generated in both English and Turkish language options.
            </div>
          </div>
"""

lines[start_idx:closing_div_idx+1] = [new_reports_tab_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("index.html Reports tab replaced successfully")
