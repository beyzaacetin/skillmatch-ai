import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'hr_interview\'"' in line:
        start_idx = idx
        break

end_idx = -1
for idx, line in enumerate(lines):
    if 'v-if="workspaceTab === \'final_decision\'"' in line:
        end_idx = idx
        break

if start_idx == -1 or end_idx == -1:
    print(f"Failed to find interview blocks. start_idx={start_idx}, end_idx={end_idx}")
    sys.exit(1)

closing_div_idx = -1
for i in range(end_idx - 1, start_idx, -1):
    if "</div>" in lines[i]:
        closing_div_idx = i
        break

if closing_div_idx == -1:
    print("Failed to find closing div of tech_interview tab")
    sys.exit(1)

print(f"Replacing interview tabs from line {start_idx+1} to {closing_div_idx+1}")

new_interviews_tab_html = """          <!-- TAB: UNIFIED INTERVIEWS MODULE -->
          <div v-if="workspaceTab === 'interviews'">
            <div style="display: grid; grid-template-columns: 1.1fr 2.5fr; gap: 24px;">
              <!-- Left panel: Question List & Candidate Selection -->
              <div>
                <!-- Candidate Selector -->
                <div class="card" style="margin-bottom:16px; border-radius:20px;">
                  <div class="card-hdr" style="padding:14px 16px; background:var(--g50);"><span class="card-title" style="font-weight:700;">Select Candidate</span></div>
                  <div class="card-body" style="padding:0; max-height:160px; overflow-y:auto;">
                    <div v-for="c in candidates.filter(cand => cand.position_id === selectedPosition.id && cand.is_active)" :key="c.id"
                         class="leaderboard-item" style="cursor:pointer; padding:10px 14px; border-bottom: 1px solid var(--border); transition:all 0.15s;"
                         :style="selectedCandidate && selectedCandidate.id === c.id ? 'background-color: var(--primary-light); border-left:3px solid var(--primary);' : ''"
                         @click="selectedCandidate = c; currentHrStep = 0; currentTechStep = 0;">
                      <div>
                        <div style="font-weight:600; font-size:13px; color:var(--text-primary); margin-bottom:2px;">{{ c.name }}</div>
                        <div style="font-size:10.5px; color:var(--text-secondary);">Stage: {{ c.status }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Questions Selector & List -->
                <div v-if="selectedCandidate" class="card" style="border-radius:20px;">
                  <div class="card-hdr" style="padding:14px 16px; background:var(--g50); display:flex; flex-direction:column; gap:10px;">
                    <span class="card-title" style="font-weight:700;">Interview Category</span>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; width:100%;">
                      <button class="btn btn-sm" :class="activeInterviewType === 'hr' ? 'btn-primary' : 'btn-secondary'" @click="activeInterviewType = 'hr'" style="border-radius:8px; justify-content:center;">HR</button>
                      <button class="btn btn-sm" :class="activeInterviewType === 'tech' ? 'btn-primary' : 'btn-secondary'" @click="activeInterviewType = 'tech'" style="border-radius:8px; justify-content:center;">Technical</button>
                    </div>
                  </div>
                  <div class="card-body" style="padding:0;">
                    <!-- HR Questions List -->
                    <template v-if="activeInterviewType === 'hr'">
                      <div v-if="!selectedCandidate.hr_interview_questions || !selectedCandidate.hr_interview_questions.length" style="padding:20px; text-align:center;">
                        <button class="btn btn-primary btn-sm" :disabled="hrQuestionsLoading" @click="startHrQuestions(selectedCandidate)" style="border-radius:8px; width:100%; justify-content:center;">Generate HR Questions</button>
                      </div>
                      <div v-else v-for="(q, idx) in selectedCandidate.hr_interview_questions" :key="idx"
                           style="padding:12px; border-bottom:1px solid var(--border); cursor:pointer; transition:all 0.15s;"
                           :style="currentHrStep === idx ? 'background:var(--primary-light); border-left:3px solid var(--primary);' : ''"
                           @click="currentHrStep = idx">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                          <span style="font-size:11px; font-weight:700; color:var(--primary);">Question {{ idx + 1 }}</span>
                          <span style="font-size:10px; color:var(--text-secondary); font-weight:600; text-transform:uppercase;">{{ q.category }}</span>
                        </div>
                        <div style="font-size:12px; color:var(--text-primary); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{{ q.question }}</div>
                      </div>
                    </template>

                    <!-- Technical Questions List -->
                    <template v-if="activeInterviewType === 'tech'">
                      <div v-if="!selectedCandidate.technical_interview_questions || !selectedCandidate.technical_interview_questions.length" style="padding:20px; text-align:center;">
                        <button class="btn btn-primary btn-sm" :disabled="techQuestionsLoading" @click="startTechQuestions(selectedCandidate)" style="border-radius:8px; width:100%; justify-content:center;">Generate Tech Questions</button>
                      </div>
                      <div v-else v-for="(q, idx) in selectedCandidate.technical_interview_questions" :key="idx"
                           style="padding:12px; border-bottom:1px solid var(--border); cursor:pointer; transition:all 0.15s;"
                           :style="currentTechStep === idx ? 'background:var(--primary-light); border-left:3px solid var(--primary);' : ''"
                           @click="currentTechStep = idx">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                          <span style="font-size:11px; font-weight:700; color:var(--primary);">Question {{ idx + 1 }}</span>
                          <span style="font-size:10px; color:var(--text-secondary); font-weight:600; text-transform:uppercase;">{{ q.category }}</span>
                        </div>
                        <div style="font-size:12px; color:var(--text-primary); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{{ q.question }}</div>
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Right panel: Active Question Details -->
              <div>
                <div v-if="!selectedCandidate" class="card" style="text-align:center; padding:60px; color:var(--text-secondary); border-radius:20px;">
                  Select a candidate from the left list to begin the interview flow.
                </div>
                <div v-else class="card" style="padding:24px; border-radius:20px;">
                  <!-- HR Active Question Details -->
                  <template v-if="activeInterviewType === 'hr'">
                    <div v-if="!selectedCandidate.hr_interview_questions || !selectedCandidate.hr_interview_questions.length" style="text-align:center; padding:40px; color:var(--text-secondary);">
                      AI HR Questions are not generated yet. Use the button in the left panel to generate them.
                    </div>
                    <div v-else-if="selectedCandidate.hr_interview_answers[currentHrStep]">
                      <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                          <span style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em;">{{ selectedCandidate.hr_interview_answers[currentHrStep].category }}</span>
                          <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:4px 0 0 0;">Question {{ currentHrStep + 1 }} of {{ selectedCandidate.hr_interview_questions.length }}</h3>
                        </div>
                        <!-- Rating Stars -->
                        <div style="display:flex; flex-direction:column; align-items:flex-end;">
                          <span style="font-size:11px; font-weight:600; color:var(--text-secondary); margin-bottom:4px;">Score</span>
                          <div class="stars">
                            <span v-for="star in 5" :key="star" class="star" 
                                  :class="{ on: star <= (selectedCandidate.hr_interview_answers[currentHrStep].rating || 0) }"
                                  @click="selectedCandidate.hr_interview_answers[currentHrStep].rating = star"
                                  style="font-size:18px;">★</span>
                          </div>
                        </div>
                      </div>

                      <div style="background:var(--g50); padding:16px; border-radius:12px; margin-bottom:20px; font-size:14px; font-weight:600; color:var(--text-primary); border-left:4px solid var(--primary);">
                        {{ selectedCandidate.hr_interview_answers[currentHrStep].question }}
                      </div>

                      <div style="margin-bottom:20px;">
                        <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:6px;">Candidate Answer</label>
                        <textarea v-model="selectedCandidate.hr_interview_answers[currentHrStep].answer" class="fta" rows="5" placeholder="Type candidate's answer here..." style="width:100%; border-radius:12px; border:1px solid var(--border); padding:12px; font-size:13px;"></textarea>
                      </div>

                      <div style="margin-bottom:24px;">
                        <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:6px;">Recruiter Observations / Notes</label>
                        <textarea v-model="selectedCandidate.hr_interview_answers[currentHrStep].notes" class="fta" rows="3" placeholder="Add recruiter observations here..." style="width:100%; border-radius:12px; border:1px solid var(--border); padding:12px; font-size:13px;"></textarea>
                      </div>

                      <div style="display:flex; justify-content:space-between; align-items:center;">
                        <button class="btn btn-secondary" :disabled="currentHrStep === 0" @click="currentHrStep--" style="border-radius:12px;">Previous</button>
                        <div style="display:flex; gap:8px;">
                          <button class="btn btn-primary" @click="saveHrAnswers(selectedCandidate)" style="border-radius:12px; background:var(--primary-hover);">Save Answers</button>
                          <button class="btn btn-primary" :disabled="currentHrStep === selectedCandidate.hr_interview_questions.length - 1" @click="currentHrStep++" style="border-radius:12px;">Next</button>
                        </div>
                      </div>
                    </div>
                  </template>

                  <!-- Technical Active Question Details -->
                  <template v-if="activeInterviewType === 'tech'">
                    <div v-if="!selectedCandidate.technical_interview_questions || !selectedCandidate.technical_interview_questions.length" style="text-align:center; padding:40px; color:var(--text-secondary);">
                      AI Technical Questions are not generated yet. Use the button in the left panel to generate them.
                    </div>
                    <div v-else-if="selectedCandidate.technical_interview_answers[currentTechStep]">
                      <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                          <span style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em;">{{ selectedCandidate.technical_interview_answers[currentTechStep].category }}</span>
                          <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:4px 0 0 0;">Question {{ currentTechStep + 1 }} of {{ selectedCandidate.technical_interview_questions.length }}</h3>
                        </div>
                        <!-- Rating Stars -->
                        <div style="display:flex; flex-direction:column; align-items:flex-end;">
                          <span style="font-size:11px; font-weight:600; color:var(--text-secondary); margin-bottom:4px;">Score</span>
                          <div class="stars">
                            <span v-for="star in 5" :key="star" class="star" 
                                  :class="{ on: star <= (selectedCandidate.technical_interview_answers[currentTechStep].score || 0) }"
                                  @click="selectedCandidate.technical_interview_answers[currentTechStep].score = star"
                                  style="font-size:18px;">★</span>
                          </div>
                        </div>
                      </div>

                      <div style="background:var(--g50); padding:16px; border-radius:12px; margin-bottom:20px; font-size:14px; font-weight:600; color:var(--text-primary); border-left:4px solid var(--primary);">
                        {{ selectedCandidate.technical_interview_answers[currentTechStep].question }}
                      </div>

                      <div style="margin-bottom:20px;">
                        <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:6px;">Candidate Answer</label>
                        <textarea v-model="selectedCandidate.technical_interview_answers[currentTechStep].answer" class="fta" rows="5" placeholder="Type candidate's answer here..." style="width:100%; border-radius:12px; border:1px solid var(--border); padding:12px; font-size:13px;"></textarea>
                      </div>

                      <div style="margin-bottom:24px;">
                        <label style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; display:block; margin-bottom:6px;">Recruiter Observations / Notes</label>
                        <textarea v-model="selectedCandidate.technical_interview_answers[currentTechStep].notes" class="fta" rows="3" placeholder="Add recruiter observations here..." style="width:100%; border-radius:12px; border:1px solid var(--border); padding:12px; font-size:13px;"></textarea>
                      </div>

                      <div style="display:flex; justify-content:space-between; align-items:center;">
                        <button class="btn btn-secondary" :disabled="currentTechStep === 0" @click="currentTechStep--" style="border-radius:12px;">Previous</button>
                        <div style="display:flex; gap:8px;">
                          <button class="btn btn-primary" @click="saveTechAnswers(selectedCandidate)" style="border-radius:12px; background:var(--primary-hover);">Save Answers</button>
                          <button class="btn btn-primary" :disabled="currentTechStep === selectedCandidate.technical_interview_questions.length - 1" @click="currentTechStep++" style="border-radius:12px;">Next</button>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
"""

# Replace
lines[start_idx:closing_div_idx+1] = [new_interviews_tab_html]

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Unified Interviews Tab successfully written to index.html")
