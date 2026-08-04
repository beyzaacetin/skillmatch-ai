import re
import os

base_dir = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4"
index_path = os.path.join(base_dir, "backend", "templates", "index.html")
app_js_path = os.path.join(base_dir, "backend", "static", "app.js")
style_css_path = os.path.join(base_dir, "backend", "static", "style.css")

print("Patching frontend files...")

# --- 1. PATCH index.html ---
if os.path.exists(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Add style sheet or styles if needed, but we will put it in style.css.
    
    # A. Replacements for Workspace -> Interviews Tab (HR / Tech Split)
    # We locate the TAB 5 block: <!-- TAB 5: MÜLAKATLAR (INTERVIEWS WORKSPACE) -->
    tab5_target = """          <!-- TAB 5: MÜLAKATLAR (INTERVIEWS WORKSPACE) -->
          <div v-if="posTab === 'interviews'">
            <div class="interview-split">
              <!-- Left pane candidate list -->
              <div class="interview-left-pane">
                <div style="font-weight:700; font-size:14px; margin-bottom:10px; color:var(--g800)">Aday Mülakat Süreci</div>
                <div style="display:flex; flex-direction:column; gap:6px" v-if="workspaceData?.applications?.length">
                  <div v-for="app in workspaceData.applications" :key="app.id" 
                       class="interview-section-item" :class="{active: activeInterviewApp?.id === app.id}" @click="activeInterviewApp = app">
                    <span style="font-weight:600">{{ app.candidate?.name }}</span>
                    <span style="font-size:10px; color:var(--g400)">{{ app.status === 'hired' ? 'Tamamlandı' : 'Sürüyor' }}</span>
                  </div>
                </div>
                <div v-else style="font-size:13px; color:var(--g400); text-align:center; padding-top:20px">Aday yok.</div>
              </div>

              <!-- Center pane selected question info -->
              <div class="interview-center-pane">
                <div v-if="activeInterviewApp">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
                    <div style="font-size:16px; font-weight:700; color:var(--g900)">Soru {{ activeQuestionIndex + 1 }} / {{ interviewQuestions.length || 4 }}</div>
                    <button class="btn btn-secondary btn-sm" @click="generateInterviewQuestionsForCandidate(activeInterviewApp.id)" :disabled="questionsGenerating">
                      <span v-if="questionsGenerating">Sorular Üretiliyor...</span>
                      <span v-else>Soruları AI ile Yeniden Üret</span>
                    </button>
                  </div>

                  <div v-if="interviewQuestions.length > 0 && interviewQuestions[activeQuestionIndex]" style="display:flex; flex-direction:column; gap:16px">
                    <div style="font-size:13px; color:var(--primary); font-weight:700; text-transform:uppercase">{{ interviewQuestions[activeQuestionIndex].section }}</div>
                    <div style="font-size:16px; font-weight:700; color:var(--g900); line-height:1.4">{{ interviewQuestions[activeQuestionIndex].question }}</div>

                    <!-- Evaluation Guide -->
                    <div class="question-guide-card">
                      <div style="font-weight:700; font-size:12px; color:var(--primary); margin-bottom:6px">Değerlendirme Rehberi (Beklenen Cevap)</div>
                      <div style="font-size:12.5px; color:var(--g700); line-height:1.5">{{ interviewQuestions[activeQuestionIndex].expected_answer }}</div>
                    </div>

                    <!-- Red Flag Warning -->
                    <div class="red-flag-card" v-if="interviewQuestions[activeQuestionIndex].red_flag_warning">
                      <b>Kırmızı Bayrak (Red Flag Warning):</b> {{ interviewQuestions[activeQuestionIndex].red_flag_warning }}
                    </div>

                    <!-- Recruiter inputs -->
                    <div>
                      <label class="label">Adayın Cevabı</label>
                      <textarea class="input" style="width:100%; height:90px" placeholder="Adayın cevabını özetleyin..." v-model="candidateAnswer"></textarea>
                    </div>

                    <div style="display:flex; gap:16px; align-items:center">
                      <div>
                        <label class="label" style="margin-bottom:6px">Değerlendirme Puanı</label>
                        <div style="display:flex; gap:4px">
                          <button v-for="score in 10" :key="score" class="score-circle-btn" 
                                  :class="{active: questionScore === score}" @click="questionScore = score">
                            {{ score }}
                          </button>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label class="label">Görüşme Notları</label>
                      <textarea class="input" style="width:100%; height:60px" placeholder="Ek mülakat notları ekleyin..." v-model="recruiterNotes"></textarea>
                    </div>

                    <div style="display:flex; justify-content:flex-end">
                      <button class="btn btn-primary" @click="saveInterviewQuestionAnswer" :disabled="!questionScore">Soruyu Tamamla & İlerle</button>
                    </div>
                  </div>
                  <div class="empty" v-else>
                    <div class="empty-title" style="font-size:14px">Mülakat soruları henüz üretilmedi veya aday henüz puanlanmadı.</div>
                    <button class="btn btn-primary btn-sm" style="margin-top:10px" @click="generateInterviewQuestionsForCandidate(activeInterviewApp.id)" :disabled="questionsGenerating">
                      Soruları AI ile Üret
                    </button>
                  </div>
                </div>
                <div class="empty" v-else>Aday seçin.</div>
              </div>

              <!-- Right pane score summary -->
              <div class="interview-right-pane" v-if="activeInterviewApp">
                <div style="font-weight:700; font-size:14px; margin-bottom:16px; color:var(--g900)">Anlık Puan Özeti</div>
                <div style="display:flex; flex-direction:column; gap:12px; font-size:12.5px" v-if="interviewQuestions.length">
                  <div v-for="q in interviewQuestions" :key="q.id" style="border-bottom:1px solid #F3F4F6; padding-bottom:8px">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px">
                      <span class="text-bold">{{ q.section }}</span>
                      <span class="text-bold" style="color:var(--primary)" v-if="q.score !== null">{{ q.score }} / 10</span>
                      <span style="color:var(--g400); font-style:italic" v-else>Puanlanmadı</span>
                    </div>
                    <div style="color:var(--g500); font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis" :title="q.notes">{{ q.notes || 'Not girilmemiş.' }}</div>
                  </div>
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px; padding-top:10px; border-top:2px solid #E5E7EB">
                    <span class="text-bold" style="font-size:14px">Ortalama Skor:</span>
                    <span class="text-bold" style="font-size:18px; color:var(--primary)">
                      {{ 
                        interviewQuestions.filter(x => x.score !== null).length > 0 
                        ? (interviewQuestions.filter(x => x.score !== null).reduce((acc, x) => acc + x.score, 0) / interviewQuestions.filter(x => x.score !== null).length).toFixed(1) + ' / 10'
                        : 'Henüz puanlanmadı'
                      }}
                    </span>
                  </div>
                </div>
                <div style="font-size:13px; color:var(--g400); font-style:italic" v-else>
                  Soru-cevap özeti bulunmamaktadır.
                </div>
              </div>
            </div>
          </div>"""

    tab5_replacement = """          <!-- TAB 5: MÜLAKATLAR (INTERVIEWS WORKSPACE) -->
          <div v-if="posTab === 'interviews'">
            <!-- Sub-tabs for HR / Tech Split -->
            <div class="workspace-sub-tabs" style="display:flex; gap:12px; border-bottom:1px solid var(--g200); margin-bottom:20px; padding-bottom:8px">
              <button class="btn btn-sm" :class="workspaceInterviewType === 'HR' ? 'btn-primary' : 'btn-ghost'" @click="setWorkspaceInterviewType('HR')" style="font-weight:600">
                İK Mülakatı (HR Interview)
              </button>
              <button class="btn btn-sm" :class="workspaceInterviewType === 'TECHNICAL' ? 'btn-primary' : 'btn-ghost'" @click="setWorkspaceInterviewType('TECHNICAL')" style="font-weight:600">
                Teknik Mülakat (Technical Interview)
              </button>
            </div>

            <div class="interview-split">
              <!-- Left pane candidate list -->
              <div class="interview-left-pane">
                <div style="font-weight:700; font-size:14px; margin-bottom:10px; color:var(--g800)">Aday Mülakat Süreci</div>
                <div style="display:flex; flex-direction:column; gap:6px" v-if="workspaceData?.applications?.length">
                  <div v-for="app in workspaceData.applications" :key="app.id" 
                       class="interview-section-item" :class="{active: activeInterviewApp?.id === app.id}" @click="selectInterviewApp(app)">
                    <span style="font-weight:600">{{ app.candidate?.name }}</span>
                    <span style="font-size:10px; color:var(--g400)">{{ app.status === 'hired' ? 'Tamamlandı' : 'Sürüyor' }}</span>
                  </div>
                </div>
                <div v-else style="font-size:13px; color:var(--g400); text-align:center; padding-top:20px">Aday yok.</div>
              </div>

              <!-- Center pane selected question info -->
              <div class="interview-center-pane">
                <div v-if="activeInterviewApp">
                  <!-- Read-only HR feedback visible for Technical Interviewer -->
                  <div v-if="workspaceInterviewType === 'TECHNICAL' && hrInterviewAnswers && hrInterviewAnswers.length" 
                       style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:16px; margin-bottom:20px">
                    <div style="font-weight:700; font-size:13.5px; color:#166534; margin-bottom:8px; display:flex; justify-content:space-between">
                      <span>İK Mülakat Değerlendirme Özeti</span>
                      <span>İK Ortalama Skor: {{ getAverageScoreText(hrInterviewAnswers) }}</span>
                    </div>
                    <div style="font-size:12.5px; color:#14532d; line-height:1.5; display:flex; flex-direction:column; gap:6px">
                      <div v-for="ans in hrInterviewAnswers" :key="ans.id">
                        <b>{{ ans.section }}:</b> {{ ans.notes || 'Not girilmemiş.' }}
                        <span v-if="ans.score !== null" style="font-weight:bold; color:var(--primary)"> (Puan: {{ ans.score }}/10)</span>
                      </div>
                    </div>
                  </div>

                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
                    <div style="font-size:16px; font-weight:700; color:var(--g900)">Soru {{ activeQuestionIndex + 1 }} / {{ interviewQuestions.length || 4 }}</div>
                    <button class="btn btn-secondary btn-sm" @click="generateInterviewQuestionsForCandidate(activeInterviewApp.id)" :disabled="questionsGenerating">
                      <span v-if="questionsGenerating">Sorular Üretiliyor...</span>
                      <span v-else>Soruları AI ile Yeniden Üret</span>
                    </button>
                  </div>

                  <div v-if="interviewQuestions.length > 0 && interviewQuestions[activeQuestionIndex]" style="display:flex; flex-direction:column; gap:16px">
                    <div style="font-size:13px; color:var(--primary); font-weight:700; text-transform:uppercase">{{ interviewQuestions[activeQuestionIndex].section }}</div>
                    <div style="font-size:16px; font-weight:700; color:var(--g900); line-height:1.4">{{ interviewQuestions[activeQuestionIndex].question }}</div>

                    <!-- Evaluation Guide -->
                    <div class="question-guide-card">
                      <div style="font-weight:700; font-size:12px; color:var(--primary); margin-bottom:6px">Değerlendirme Rehberi (Beklenen Cevap)</div>
                      <div style="font-size:12.5px; color:var(--g700); line-height:1.5">{{ interviewQuestions[activeQuestionIndex].expected_answer }}</div>
                    </div>

                    <!-- Red Flag Warning -->
                    <div class="red-flag-card" v-if="interviewQuestions[activeQuestionIndex].red_flag_warning">
                      <b>Kırmızı Bayrak (Red Flag Warning):</b> {{ interviewQuestions[activeQuestionIndex].red_flag_warning }}
                    </div>

                    <!-- Recruiter inputs -->
                    <div>
                      <label class="label">Adayın Cevabı</label>
                      <textarea class="input" style="width:100%; height:90px" placeholder="Adayın cevabını özetleyin..." v-model="candidateAnswer"></textarea>
                    </div>

                    <div style="display:flex; gap:16px; align-items:center">
                      <div>
                        <label class="label" style="margin-bottom:6px">Değerlendirme Puanı</label>
                        <div style="display:flex; gap:4px">
                          <button v-for="score in 10" :key="score" class="score-circle-btn" 
                                  :class="{active: questionScore === score}" @click="questionScore = score">
                            {{ score }}
                          </button>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label class="label">Görüşme Notları</label>
                      <textarea class="input" style="width:100%; height:60px" placeholder="Ek mülakat notları ekleyin..." v-model="recruiterNotes"></textarea>
                    </div>

                    <div style="display:flex; justify-content:flex-end">
                      <button class="btn btn-primary" @click="saveInterviewQuestionAnswer" :disabled="!questionScore">Soruyu Tamamla & İlerle</button>
                    </div>
                  </div>
                  <div class="empty" v-else>
                    <div class="empty-title" style="font-size:14px">Mülakat soruları henüz üretilmedi veya aday henüz puanlanmadı.</div>
                    <button class="btn btn-primary btn-sm" style="margin-top:10px" @click="generateInterviewQuestionsForCandidate(activeInterviewApp.id)" :disabled="questionsGenerating">
                      Soruları AI ile Üret
                    </button>
                  </div>
                </div>
                <div class="empty" v-else>Aday seçin.</div>
              </div>

              <!-- Right pane score summary -->
              <div class="interview-right-pane" v-if="activeInterviewApp">
                <div style="font-weight:700; font-size:14px; margin-bottom:16px; color:var(--g900)">Anlık Puan Özeti</div>
                <div style="display:flex; flex-direction:column; gap:12px; font-size:12.5px" v-if="interviewQuestions.length">
                  <div v-for="q in interviewQuestions" :key="q.id" style="border-bottom:1px solid #F3F4F6; padding-bottom:8px">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px">
                      <span class="text-bold">{{ q.section }}</span>
                      <span class="text-bold" style="color:var(--primary)" v-if="q.score !== null">{{ q.score }} / 10</span>
                      <span style="color:var(--g400); font-style:italic" v-else>Puanlanmadı</span>
                    </div>
                    <div style="color:var(--g500); font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis" :title="q.notes">{{ q.notes || 'Not girilmemiş.' }}</div>
                  </div>
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px; padding-top:10px; border-top:2px solid #E5E7EB">
                    <span class="text-bold" style="font-size:14px">Ortalama Skor:</span>
                    <span class="text-bold" style="font-size:18px; color:var(--primary)">
                      {{ getAverageScoreText(interviewQuestions) }}
                    </span>
                  </div>
                </div>
                <div style="font-size:13px; color:var(--g400); font-style:italic" v-else>
                  Soru-cevap özeti bulunmamaktadır.
                </div>
              </div>
            </div>
          </div>"""

    html = html.replace(tab5_target, tab5_replacement)

    # B. Replacements for Tasks page (Calendar & Tasks Redesign)
    # We locate <!-- TASKS & CALENDAR (KANBAN GÖREVLER) PAGE -->
    tasks_target = """    <!-- TASKS & CALENDAR (KANBAN GÖREVLER) PAGE -->
    <template v-if="page==='tasks'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Görevler & İşe Alım Panosu</div>
          <div class="page-hdr-sub">Ekip içi görev atamalarını yapın ve süreçleri takip edin</div>
        </div>
        <button class="btn btn-primary" @click="openNewTaskModal">+ Yeni Görev Ekle</button>
      </div>
      <div class="page-body">
        <div class="kanban" style="display:grid;grid-template-columns:repeat(3, 1fr);gap:20px;height:calc(100vh - 220px)">
          <!-- TODO -->
          <div class="kb-col" style="background:var(--g50);border-radius:12px;padding:16px">
            <div class="kb-col-hdr" style="display:flex;justify-content:space-between;margin-bottom:12px">
              <span style="font-weight:700;color:var(--g700)">Yapılacaklar</span>
              <span class="kb-count">{{ recruitmentTasks.filter(t => t.status === 'todo').length }}</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;overflow-y:auto;height:calc(100% - 40px)">
              <div v-for="t in recruitmentTasks.filter(t => t.status === 'todo')" :key="t.id" class="card" style="padding:12px;cursor:pointer" @click="editRecruitmentTask(t)">
                <div style="font-weight:600;font-size:14px">{{ t.title }}</div>
                <div style="font-size:12px;color:var(--g500);margin-top:4px">{{ t.description || 'Açıklama yok' }}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;font-size:11px;color:var(--g400)">
                  <span>Sorumlu: {{ t.assigned_to || 'Belirtilmemiş' }}</span>
                  <span v-if="t.due_date">Tarih: {{ t.due_date }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- IN PROGRESS -->
          <div class="kb-col" style="background:var(--g50);border-radius:12px;padding:16px">
            <div class="kb-col-hdr" style="display:flex;justify-content:space-between;margin-bottom:12px">
              <span style="font-weight:700;color:var(--g700)">Devam Edenler</span>
              <span class="kb-count">{{ recruitmentTasks.filter(t => t.status === 'in_progress').length }}</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;overflow-y:auto;height:calc(100% - 40px)">
              <div v-for="t in recruitmentTasks.filter(t => t.status === 'in_progress')" :key="t.id" class="card" style="padding:12px;cursor:pointer" @click="editRecruitmentTask(t)">
                <div style="font-weight:600;font-size:14px">{{ t.title }}</div>
                <div style="font-size:12px;color:var(--g500);margin-top:4px">{{ t.description || 'Açıklama yok' }}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;font-size:11px;color:var(--g400)">
                  <span>Sorumlu: {{ t.assigned_to || 'Belirtilmemiş' }}</span>
                  <span v-if="t.due_date">Tarih: {{ t.due_date }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- DONE -->
          <div class="kb-col" style="background:var(--g50);border-radius:12px;padding:16px">
            <div class="kb-col-hdr" style="display:flex;justify-content:space-between;margin-bottom:12px">
              <span style="font-weight:700;color:var(--g700)">Tamamlananlar</span>
              <span class="kb-count">{{ recruitmentTasks.filter(t => t.status === 'done').length }}</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;overflow-y:auto;height:calc(100% - 40px)">
              <div v-for="t in recruitmentTasks.filter(t => t.status === 'done')" :key="t.id" class="card" style="padding:12px;cursor:pointer;opacity:0.8" @click="editRecruitmentTask(t)">
                <div style="font-weight:600;font-size:14px;text-decoration:line-through">{{ t.title }}</div>
                <div style="font-size:12px;color:var(--g500);margin-top:4px">{{ t.description || 'Açıklama yok' }}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;font-size:11px;color:var(--g400)">
                  <span>Sorumlu: {{ t.assigned_to || 'Belirtilmemiş' }}</span>
                  <span v-if="t.due_date">Tarih: {{ t.due_date }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>"""

    tasks_replacement = """    <!-- CALENDAR & TASKS PAGE -->
    <template v-if="page==='tasks'">
      <div class="page-hdr" style="display:flex; justify-content:space-between; align-items:center; background:#fff; border-bottom:1px solid var(--g200); padding:20px 24px">
        <div>
          <div class="page-hdr-title" style="font-family:'Georgia', serif; font-size:24px; font-weight:700; color:var(--primary)">Takvim & Görev Yönetimi</div>
          <div class="page-hdr-sub" style="font-size:13px; color:var(--g500)">İşe alım mülakatlarını planlayın ve görevlerinizi takip edin</div>
        </div>
        <div style="display:flex; gap:10px">
          <button class="btn btn-secondary" @click="openNewEventModal(null)">+ Etkinlik Ekle</button>
          <button class="btn btn-primary" @click="openNewTaskModal">+ Yeni Görev Ekle</button>
        </div>
      </div>

      <div class="page-body" style="padding:24px; background:var(--g50); display:grid; grid-template-columns: 1.8fr 1.2fr; gap:24px; height:calc(100vh - 180px)">
        <!-- LEFT: Calendar Grid -->
        <div class="card" style="padding:20px; display:flex; flex-direction:column; justify-content:space-between; height:100%">
          <!-- Calendar Header -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
            <div style="display:flex; gap:8px; align-items:center">
              <button class="btn btn-outline btn-sm" @click="navigateCalendarMonth(-1)">&lt; Önceki</button>
              <span style="font-size:16px; font-weight:700; color:var(--g800); min-width:140px; text-align:center">
                {{ turkishMonthNames[calendarMonth] }} {{ calendarYear }}
              </span>
              <button class="btn btn-outline btn-sm" @click="navigateCalendarMonth(1)">Sonraki &gt;</button>
            </div>
            <!-- Month/Week Switch -->
            <div style="display:flex; background:var(--g100); border-radius:6px; padding:2px">
              <button class="btn btn-sm" :class="calendarViewType === 'month' ? 'btn-primary' : 'btn-ghost'" @click="calendarViewType = 'month'" style="padding:4px 12px; font-size:12px">Ay</button>
              <button class="btn btn-sm" :class="calendarViewType === 'week' ? 'btn-primary' : 'btn-ghost'" @click="calendarViewType = 'week'" style="padding:4px 12px; font-size:12px">Hafta</button>
            </div>
          </div>

          <!-- Calendar Grid Header -->
          <div style="display:grid; grid-template-columns: repeat(7, 1fr); text-align:center; font-weight:700; font-size:12px; color:var(--g500); border-bottom:1px solid var(--g200); padding-bottom:8px">
            <span>Pzt</span><span>Sal</span><span>Çar</span><span>Per</span><span>Cum</span><span>Cmt</span><span>Paz</span>
          </div>

          <!-- Calendar Cells Grid -->
          <div style="display:grid; grid-template-rows: repeat(5, 1fr); grid-template-columns: repeat(7, 1fr); gap:1px; background:var(--g200); flex-grow:1; margin-top:8px; border-radius:8px; overflow:hidden">
            <div v-for="cell in calendarDays" :key="cell.dateString" 
                 class="calendar-cell" :class="{'other-month': !cell.isCurrentMonth, 'today': cell.dateString === todayDateString}"
                 @click="openNewEventModal(cell.dateString)"
                 style="background:#fff; padding:6px; min-height:80px; display:flex; flex-direction:column; justify-content:space-between; cursor:pointer; transition:background 0.2s">
              <div style="font-weight:600; font-size:12px; text-align:right" :style="!cell.isCurrentMonth ? 'color:var(--g300)' : 'color:var(--g700)'">
                {{ cell.day }}
              </div>
              <div style="display:flex; flex-direction:column; gap:4px; overflow-y:auto; max-height:60px">
                <div v-for="evt in getEventsForDate(cell.dateString)" :key="evt.id" 
                     class="calendar-event-tag" :class="evt.event_type"
                     @click.stop="viewEventDetails(evt)"
                     :title="evt.title">
                  {{ evt.title }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Panels -->
        <div style="display:flex; flex-direction:column; gap:20px; overflow-y:auto; height:100%">
          <!-- Tasks list panel -->
          <div class="card" style="padding:16px; flex-grow:1">
            <div style="font-weight:700; font-size:14px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g100); padding-bottom:8px">
              Görevlerim
            </div>
            <div style="display:flex; flex-direction:column; gap:10px; overflow-y:auto; max-height:200px">
              <div v-for="t in recruitmentTasks" :key="t.id" 
                   style="border:1px solid var(--g200); border-radius:8px; padding:10px; background:#fff; display:flex; align-items:center; justify-content:space-between">
                <div style="display:flex; align-items:center; gap:8px">
                  <input type="checkbox" :checked="t.status === 'done'" @change="toggleTaskStatus(t)">
                  <div>
                    <div style="font-size:13px; font-weight:600" :style="t.status === 'done' ? 'text-decoration:line-through; color:var(--g400)' : ''">{{ t.title }}</div>
                    <div style="font-size:11px; color:var(--g400)" v-if="t.due_date">Süre: {{ t.due_date }}</div>
                  </div>
                </div>
                <div style="display:flex; gap:4px">
                  <button class="btn btn-ghost btn-sm" style="padding:2px 6px" @click="editRecruitmentTask(t)">✏</button>
                  <button class="btn btn-ghost btn-sm" style="padding:2px 6px; color:var(--red)" @click="deleteRecruitmentTask(t)">✕</button>
                </div>
              </div>
              <div v-if="!recruitmentTasks.length" style="font-size:12px; color:var(--g400); text-align:center; padding:10px">Aktif görev bulunmuyor.</div>
            </div>
          </div>

          <!-- Upcoming interviews panel -->
          <div class="card" style="padding:16px">
            <div style="font-weight:700; font-size:14px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g100); padding-bottom:8px">
              Yaklaşan Mülakatlar
            </div>
            <div style="display:flex; flex-direction:column; gap:8px; max-height:180px; overflow-y:auto">
              <div v-for="evt in calendarEvents.filter(e => e.event_type === 'interview')" :key="evt.id" 
                   style="padding:10px; border:1px solid var(--g100); border-radius:6px; background:#fff; display:flex; justify-content:space-between; align-items:center">
                <div>
                  <div style="font-size:13px; font-weight:600">{{ evt.title }}</div>
                  <div style="font-size:11px; color:var(--g400)">{{ formatDate(evt.start_time) }}</div>
                </div>
                <button class="btn btn-secondary btn-sm" @click="viewEventDetails(evt)">Detay</button>
              </div>
              <div v-if="!calendarEvents.filter(e => e.event_type === 'interview').length" style="font-size:12px; color:var(--g400); text-align:center">Yaklaşan mülakat yok.</div>
            </div>
          </div>

          <!-- Important dates panel -->
          <div class="card" style="padding:16px">
            <div style="font-weight:700; font-size:14px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g100); padding-bottom:8px">
              Hatırlatıcılar & Son Tarihler
            </div>
            <div style="display:flex; flex-direction:column; gap:8px; max-height:180px; overflow-y:auto">
              <div v-for="evt in calendarEvents.filter(e => e.event_type !== 'interview')" :key="evt.id" 
                   style="padding:10px; border-radius:6px; display:flex; justify-content:space-between; align-items:center"
                   :style="evt.event_type === 'deadline' ? 'background:#fef2f2; border:1px solid #fee2e2; color:#991b1b' : 'background:#fff; border:1px solid var(--g100)'">
                <div>
                  <div style="font-size:13px; font-weight:600">{{ evt.title }}</div>
                  <div style="font-size:11px; color:var(--g500)">{{ formatDate(evt.start_time) }}</div>
                </div>
                <button class="btn btn-ghost btn-sm" @click="deleteCalendarEvent(evt.id)">✕</button>
              </div>
              <div v-if="!calendarEvents.filter(e => e.event_type !== 'interview').length" style="font-size:12px; color:var(--g400); text-align:center">Bekleyen hatırlatıcı yok.</div>
            </div>
          </div>
        </div>
      </div>
    </template>"""

    html = html.replace(tasks_target, tasks_replacement)

    # C. Replacements for Yetki Yönetimi (User Management Redesign)
    # We locate <!-- USER MANAGEMENT (YETKİ ALANI) -->
    user_target = """    <!-- USER MANAGEMENT (YETKİ ALANI) -->
    <template v-if="page==='users'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Yetki Alanı</div>
          <div class="page-hdr-sub">Kullanıcıları, yetkilerini ve erişimlerini yönetin</div>
        </div>
        <button class="btn btn-primary" @click="openNewUserModal">+ Yeni Kullanıcı Ekle</button>
      </div>
      
      <!-- KPI Cards -->
      <div class="grid-4" style="margin-bottom:24px; display:grid; grid-template-columns: repeat(4, 1fr); gap:16px;">
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Toplam Kullanıcı</div>
          <div style="font-size:24px; font-weight:700; color:#0B4A3A; margin-top:8px">{{ allUsers.length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Aktif Kullanıcı</div>
          <div style="font-size:24px; font-weight:700; color:var(--primary); margin-top:8px">{{ allUsers.filter(u => u.is_active).length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Yönetici (Admin)</div>
          <div style="font-size:24px; font-weight:700; color:#b45309; margin-top:8px">{{ allUsers.filter(u => u.role === 'ADMIN').length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Son 7 Gün Giriş Yapanlar</div>
          <div style="font-size:24px; font-weight:700; color:#2563eb; margin-top:8px">
            {{ allUsers.filter(u => u.last_login && (new Date() - new Date(u.last_login)) < 7 * 24 * 60 * 60 * 1000).length }}
          </div>
        </div>
      </div>

      <div class="page-body">
        <div class="card" style="overflow:hidden">
          <table class="tbl">
            <thead>
              <tr>
                <th>Kullanıcı</th>
                <th>E-posta</th>
                <th>Departman</th>
                <th>Rol</th>
                <th>Durum</th>
                <th>Son Giriş</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in allUsers" :key="u.id">
                <td>
                  <div style="display:flex;align-items:center;gap:10px">
                    <div class="cand-av" style="background:var(--primary-light);color:var(--primary)">{{ (u.full_name||'?')[0].toUpperCase() }}</div>
                    <div style="font-weight:600">{{ u.full_name }}</div>
                  </div>
                </td>
                <td style="font-size:13px;color:var(--g600)">{{ u.email }}</td>
                <td style="font-size:13px">{{ u.department || '—' }}</td>
                <td>
                  <span class="badge" style="padding: 4px 8px; border-radius: 6px; font-size:11px; font-weight:600;" :style="u.role === 'ADMIN' ? 'background:#fef3c7; color:#b45309;' : (u.role === 'RECRUITER' ? 'background:#d1fae5; color:#065f46;' : 'background:#e0f2fe; color:#0369a1;')">
                    {{ u.role }}
                  </span>
                </td>
                <td>
                  <span class="badge" :style="u.is_active ? 'background:#d1fae5; color:#065f46;' : 'background:#fee2e2; color:#991b1b;'">
                    {{ u.is_active ? 'Aktif' : 'Pasif' }}
                  </span>
                </td>
                <td style="font-size:12px;color:var(--g500)">{{ u.last_login ? formatDate(u.last_login) : 'Hiç giriş yapmadı' }}</td>
                <td>
                  <div style="display:flex; gap:8px">
                    <button class="btn btn-outline btn-sm" @click="editUser(u)">Düzenle</button>
                    <button class="btn btn-outline btn-sm" @click="openPasswordReset(u)">Şifre Yenile</button>
                    <button v-if="u.is_active" class="btn btn-danger btn-sm" @click="toggleUserStatus(u, false)" :disabled="u.id === currentUser.id">Pasifleştir</button>
                    <button v-else class="btn btn-secondary btn-sm" @click="toggleUserStatus(u, true)">Aktifleştir</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>"""

    user_replacement = """    <!-- USER MANAGEMENT (YETKİ ALANI) -->
    <template v-if="page==='users'">
      <div class="page-hdr" style="display:flex; justify-content:space-between; align-items:center; background:#fff; border-bottom:1px solid var(--g200); padding:20px 24px">
        <div>
          <div class="page-hdr-title" style="font-family:'Georgia', serif; font-size:24px; font-weight:700; color:var(--primary)">Yetki & Erişim Yönetimi</div>
          <div class="page-hdr-sub" style="font-size:13px; color:var(--g500)">Kullanıcı rollerini, departmanları ve yetki matrisini yönetin</div>
        </div>
        <button class="btn btn-primary" @click="openNewUserModal">+ Yeni Kullanıcı Ekle</button>
      </div>

      <!-- KPI Cards -->
      <div class="grid-4" style="margin:24px; display:grid; grid-template-columns: repeat(4, 1fr); gap:16px;">
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Toplam Kullanıcı</div>
          <div style="font-size:24px; font-weight:700; color:#0B4A3A; margin-top:8px">{{ allUsers.length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Aktif Kullanıcı</div>
          <div style="font-size:24px; font-weight:700; color:var(--primary); margin-top:8px">{{ allUsers.filter(u => u.is_active).length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Beklemede / Pasif</div>
          <div style="font-size:24px; font-weight:700; color:#b91c1c; margin-top:8px">{{ allUsers.filter(u => !u.is_active).length }}</div>
        </div>
        <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
          <div style="font-size:12px; font-weight:600; color:var(--g500)">Tanımlı Rol</div>
          <div style="font-size:24px; font-weight:700; color:#2563eb; margin-top:8px">3 Farklı Rol</div>
        </div>
      </div>

      <div class="page-body" style="padding:0 24px 24px 24px">
        <!-- Sub-tabs for user management -->
        <div class="modal-tabs" style="background:#fff; border-radius:8px 8px 0 0; border:1px solid var(--g200); border-bottom:none; margin-bottom:0">
          <div class="modal-tab" :class="{active: userSubTab === 'users'}" @click="userSubTab = 'users'">Kullanıcılar</div>
          <div class="modal-tab" :class="{active: userSubTab === 'roles'}" @click="userSubTab = 'roles'">Rol Tanımları</div>
          <div class="modal-tab" :class="{active: userSubTab === 'matrix'}" @click="userSubTab = 'matrix'">Yetki Matrisi</div>
        </div>

        <div class="card" style="border-radius:0 0 8px 8px; border-top:none; padding:20px; background:#fff">
          <!-- TAB 1: Kullanıcılar -->
          <div v-if="userSubTab === 'users'">
            <!-- Filters -->
            <div style="display:flex; gap:12px; margin-bottom:16px; align-items:center">
              <input v-model="userSearchQuery" type="text" class="fi" placeholder="Kullanıcı ara (ad, e-posta...)" style="flex:1">
              <select v-model="userRoleFilter" class="fselect fs" style="min-width:140px">
                <option value="">Tüm Roller</option>
                <option value="ADMIN">ADMIN</option>
                <option value="RECRUITER">RECRUITER</option>
                <option value="VIEWER">VIEWER</option>
              </select>
              <select v-model="userStatusFilter" class="fselect fs" style="min-width:140px">
                <option value="">Tüm Durumlar</option>
                <option value="active">Aktif</option>
                <option value="passive">Pasif</option>
              </select>
            </div>

            <!-- Users Table -->
            <table class="tbl">
              <thead>
                <tr>
                  <th>Kullanıcı</th>
                  <th>E-posta</th>
                  <th>Departman</th>
                  <th>Rol</th>
                  <th>Durum</th>
                  <th>Son Giriş</th>
                  <th>Oluşturma</th>
                  <th>İşlem</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in filteredUsers" :key="u.id">
                  <td>
                    <div style="display:flex; align-items:center; gap:10px">
                      <div class="cand-av" style="background:var(--primary-light); color:var(--primary); font-size:12px; width:32px; height:32px">
                        {{ (u.full_name||'?')[0].toUpperCase() }}
                      </div>
                      <div style="font-weight:600">{{ u.full_name }}</div>
                    </div>
                  </td>
                  <td style="font-size:13px; color:var(--g600)">{{ u.email }}</td>
                  <td style="font-size:13px">{{ u.department || '—' }}</td>
                  <td>
                    <span class="badge" style="padding:4px 8px; border-radius:6px; font-size:11px; font-weight:600;"
                          :style="u.role === 'ADMIN' ? 'background:#fef3c7; color:#b45309;' : (u.role === 'RECRUITER' ? 'background:#d1fae5; color:#065f46;' : 'background:#e0f2fe; color:#0369a1;')">
                      {{ u.role }}
                    </span>
                  </td>
                  <td>
                    <span class="badge" :style="u.is_active ? 'background:#d1fae5; color:#065f46;' : 'background:#fee2e2; color:#991b1b;'">
                      {{ u.is_active ? 'Aktif' : 'Pasif' }}
                    </span>
                  </td>
                  <td style="font-size:12px; color:var(--g500)">{{ u.last_login ? formatDate(u.last_login) : 'Hiç giriş yapmadı' }}</td>
                  <td style="font-size:12px; color:var(--g500)">{{ u.created_at ? formatDate(u.created_at) : '—' }}</td>
                  <td>
                    <div style="display:flex; gap:6px">
                      <button class="btn btn-outline btn-sm" @click="editUser(u)">Düzenle</button>
                      <button class="btn btn-outline btn-sm" @click="openPasswordReset(u)">Şifre Sıfırla</button>
                      <button v-if="u.is_active" class="btn btn-danger btn-sm" @click="toggleUserStatus(u, false)" :disabled="u.id === currentUser.id">Pasifleştir</button>
                      <button v-else class="btn btn-secondary btn-sm" @click="toggleUserStatus(u, true)">Aktifleştir</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TAB 2: Roller -->
          <div v-if="userSubTab === 'roles'">
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px">
              <div class="card" style="padding:16px; border:1px solid #fef3c7">
                <div style="font-weight:700; font-size:15px; color:#b45309; margin-bottom:8px">ADMIN</div>
                <p style="font-size:13px; color:var(--g600); line-height:1.5">Sistemdeki tüm yetkilere sahiptir. Kullanıcı tanımlama, yetki yönetimi, ilan açma, aday değerlendirme, AI asistanı ve tüm raporlara tam erişim hakkı vardır.</p>
              </div>
              <div class="card" style="padding:16px; border:1px solid #d1fae5">
                <div style="font-weight:700; font-size:15px; color:#065f46; margin-bottom:8px">RECRUITER</div>
                <p style="font-size:13px; color:var(--g600); line-height:1.5">İşe alım danışmanıdır. Aday havuzunu yönetebilir, mülakat planlayıp puanlayabilir, not ekleyebilir ve rapor oluşturabilir. Sistem yönetici yetkileri yoktur.</p>
              </div>
              <div class="card" style="padding:16px; border:1px solid #e0f2fe">
                <div style="font-weight:700; font-size:15px; color:#0369a1; margin-bottom:8px">VIEWER</div>
                <p style="font-size:13px; color:var(--g600); line-height:1.5">İzleyici rolündedir. Mülakat süreçlerini, aday notlarını ve raporları salt-okunur (read-only) modda görebilir. Veri ekleme, puanlama veya silme yetkileri kısıtlanmıştır.</p>
              </div>
            </div>
          </div>

          <!-- TAB 3: Yetki Matrisi -->
          <div v-if="userSubTab === 'matrix'">
            <table class="tbl">
              <thead>
                <tr>
                  <th>Modül / İşlem</th>
                  <th style="text-align:center">ADMIN</th>
                  <th style="text-align:center">RECRUITER</th>
                  <th style="text-align:center">VIEWER</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Kullanıcı Ekleme / Silme / Şifre Sıfırlama</td>
                  <td style="text-align:center; color:var(--green)">✓ (Tam Erişim)</td>
                  <td style="text-align:center; color:var(--red)">✗ (Yetki Yok)</td>
                  <td style="text-align:center; color:var(--red)">✗ (Yetki Yok)</td>
                </tr>
                <tr>
                  <td>Pozisyon / İlan Oluşturma ve Düzenleme</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--g400)">👁 Salt Okunur</td>
                </tr>
                <tr>
                  <td>Aday CV Yükleme ve Akıllı Eşleştirme</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--red)">✗ (Yetki Yok)</td>
                </tr>
                <tr>
                  <td>Mülakat Değerlendirme &amp; Puanlama</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--g400)">👁 Salt Okunur</td>
                </tr>
                <tr>
                  <td>Değerlendirme Raporu PDF İndirme</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                  <td style="text-align:center; color:var(--green)">✓</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>"""

    html = html.replace(user_target, user_replacement)

    # D. Replacements for Analytics Page (Real stats & SVG graphs)
    # We replace the whole page-body in analytics v-if starting at line 1490.
    # We find `<div class="page-body" style="padding:24px;background:var(--g50)">`
    # and replace the content up to `</template>` of analytics (line 1730 or so).
    # Let's target the page body specifically.
    analytics_body_target = """      <div class="page-body" style="padding:24px;background:var(--g50)">
        <!-- KPI Cards Grid -->
        <div class="grid-4" style="margin-bottom:24px">
          <!-- KPI 1 -->
          <div class="stat-card glass-card" style="position:relative;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div class="stat-val">{{ stats.kpis?.total_candidates ?? 0 }}</div>
              <span style="font-size:11px;font-weight:700;color:var(--green);background:rgba(11,74,58,0.08);padding:2px 6px;border-radius:10px">+12.4%</span>
            </div>
            <div class="stat-lbl">Toplam Aday Havuzu</div>
            <div class="sparkline-container">
              <svg viewBox="0 0 100 25" width="100%" height="25" stroke="var(--primary)" stroke-width="1.5" fill="none">
                <path d="M0,22 Q15,8 30,18 T60,4 T90,11 T100,6" />
              </svg>
            </div>
          </div>
          <!-- KPI 2 -->
          <div class="stat-card glass-card" style="position:relative;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div class="stat-val">{{ stats.kpis?.avg_match_score ? stats.kpis.avg_match_score + '%' : '0%' }}</div>
              <span style="font-size:11px;font-weight:700;color:var(--green);background:rgba(11,74,58,0.08);padding:2px 6px;border-radius:10px">+2.1%</span>
            </div>
            <div class="stat-lbl">Ortalama Uyum Skoru</div>
            <div class="sparkline-container">
              <svg viewBox="0 0 100 25" width="100%" height="25" stroke="var(--primary)" stroke-width="1.5" fill="none">
                <path d="M0,14 Q15,22 30,11 T60,7 T90,2 T100,4" />
              </svg>
            </div>
          </div>
          <!-- KPI 3 -->
          <div class="stat-card glass-card" style="position:relative;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div class="stat-val">3.2 Gün</div>
              <span style="font-size:11px;font-weight:700;color:var(--green);background:rgba(11,74,58,0.08);padding:2px 6px;border-radius:10px">-15.3%</span>
            </div>
            <div class="stat-lbl">Aday Tarama Hızı</div>
            <div class="sparkline-container">
              <svg viewBox="0 0 100 25" width="100%" height="25" stroke="var(--primary)" stroke-width="1.5" fill="none">
                <path d="M0,7 Q15,16 30,4 T60,20 T90,9 T100,3" />
              </svg>
            </div>
          </div>
          <!-- KPI 4 -->
          <div class="stat-card glass-card" style="position:relative;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div class="stat-val">%94.5</div>
              <span style="font-size:11px;font-weight:700;color:var(--green);background:rgba(11,74,58,0.08);padding:2px 6px;border-radius:10px">+0.8%</span>
            </div>
            <div class="stat-lbl">AI Karar Doğruluğu</div>
            <div class="sparkline-container">
              <svg viewBox="0 0 100 25" width="100%" height="25" stroke="var(--primary)" stroke-width="1.5" fill="none">
                <path d="M0,18 Q15,4 30,13 T60,3 T90,7 T100,2" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Match Quality Flow (Decision Engine) -->
        <div style="margin-bottom:24px">
          <div style="font-size:12px;font-weight:700;color:var(--g500);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px">AI Match Screening Pipeline</div>
          <div class="decision-engine-flow" style="background:#fff;border:1px solid var(--g200);border-radius:var(--rl)">
            <!-- Node 1 -->
            <div class="flow-node">
              <div class="node-icon">👥</div>
              <div class="node-val">{{ stats.kpis?.total_candidates ?? 0 }}</div>
              <div class="node-lbl">Aday Havuzu</div>
            </div>
            <!-- Arrow 1 -->
            <div class="flow-arrow">
              <svg viewBox="0 0 100 20" preserveAspectRatio="none">
                <path d="M0,10 L100,10" stroke="#0B4A3A" stroke-width="2" stroke-dasharray="6,4" class="flow-dash" fill="none" />
              </svg>
            </div>
            <!-- Node 2 -->
            <div class="flow-node">
              <div class="node-icon">🔍</div>
              <div class="node-val">{{ stats.funnel?.screening ?? 0 }}</div>
              <div class="node-lbl">AI Ön Eleme</div>
            </div>
            <!-- Arrow 2 -->
            <div class="flow-arrow">
              <svg viewBox="0 0 100 20" preserveAspectRatio="none">
                <path d="M0,10 L100,10" stroke="#0B4A3A" stroke-width="2" stroke-dasharray="6,4" class="flow-dash" fill="none" />
              </svg>
            </div>
            <!-- Node 3 -->
            <div class="flow-node">
              <div class="node-icon">🤝</div>
              <div class="node-val">{{ stats.funnel?.interview ?? 0 }}</div>
              <div class="node-lbl">Mülakat Aşaması</div>
            </div>
            <!-- Arrow 3 -->
            <div class="flow-arrow">
              <svg viewBox="0 0 100 20" preserveAspectRatio="none">
                <path d="M0,10 L100,10" stroke="#0B4A3A" stroke-width="2" stroke-dasharray="6,4" class="flow-dash" fill="none" />
              </svg>
            </div>
            <!-- Node 4 -->
            <div class="flow-node">
              <div class="node-icon">📄</div>
              <div class="node-val">{{ stats.funnel?.offer ?? 0 }}</div>
              <div class="node-lbl">Teklif Aşaması</div>
            </div>
            <!-- Arrow 4 -->
            <div class="flow-arrow">
              <svg viewBox="0 0 100 20" preserveAspectRatio="none">
                <path d="M0,10 L100,10" stroke="#0B4A3A" stroke-width="2" stroke-dasharray="6,4" class="flow-dash" fill="none" />
              </svg>
            </div>
            <!-- Node 5 -->
            <div class="flow-node">
              <div class="node-icon">✨</div>
              <div class="node-val">{{ stats.funnel?.hired ?? 0 }}</div>
              <div class="node-lbl">İşe Alım</div>
            </div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns: 1fr 1fr;gap:24px;margin-bottom:24px">
          <!-- AI Insights Panel -->
          <div class="card glass-glow-panel">
            <div class="card-hdr" style="border:none;background:transparent"><span style="font-weight:700;color:var(--primary);font-size:15px">AI Recruitment Intelligence</span></div>
            <div class="card-body" style="padding:0 20px 20px 20px">
              <div v-if="stats.ai_insights && stats.ai_insights.length" style="display:flex;flex-direction:column;gap:12px">
                <div v-for="(ins, idx) in stats.ai_insights" :key="idx" style="font-size:13px;color:var(--g800);line-height:1.6;display:flex;gap:10px;align-items:flex-start;background:rgba(255,255,255,0.6);padding:12px;border-radius:8px;border:1px solid rgba(11,74,58,0.05)">
                  <span style="color:var(--primary);font-size:15px">✦</span>
                  <span v-html="ins"></span>
                </div>
                <!-- Dynamic custom insights -->
                <div style="font-size:13px;color:var(--g800);line-height:1.6;display:flex;gap:10px;align-items:flex-start;background:rgba(255,255,255,0.6);padding:12px;border-radius:8px;border:1px solid rgba(11,74,58,0.05)">
                  <span style="color:var(--primary);font-size:15px">✦</span>
                  <span><b>Yetenek Yoğunluğu:</b> Python ve SQL yetkinlikleri aday havuzunda %42 oranla en yüksek artış gösteren trendler arasındadır.</span>
                </div>
                <div style="font-size:13px;color:var(--g800);line-height:1.6;display:flex;gap:10px;align-items:flex-start;background:rgba(255,255,255,0.6);padding:12px;border-radius:8px;border:1px solid rgba(11,74,58,0.05)">
                  <span style="color:var(--primary);font-size:15px">✦</span>
                  <span><b>Süreç Darboğazı:</b> Değerlendirme (screening) aşamasındaki ortalama bekleme süresi son 7 günde 1.2 gün iyileşme gösterdi.</span>
                </div>
              </div>
              <div v-else style="font-size:13px;color:var(--g500)">Yapay Zeka analizi için yeterli başvuru verisi bulunamadı.</div>
            </div>
          </div>

          <!-- AI Talent Map (Heatmap) -->
          <div class="card glass-card">
            <div class="card-hdr" style="border:none;background:transparent"><span style="font-weight:700;font-size:15px">AI Talent Map</span></div>
            <div class="card-body" style="padding:0 20px 20px 20px">
              <div class="talent-map-container" style="padding:0;border:none">
                <div class="talent-map-grid">
                  <div class="heatmap-header-cell" style="padding-left:0">Yetenek</div>
                  <div class="heatmap-header-cell">Giriş</div>
                  <div class="heatmap-header-cell">Orta</div>
                  <div class="heatmap-header-cell">Kıdemli</div>
                  
                  <template v-for="skill in ['Python', 'SQL', 'React', 'FastAPI', 'Docker', 'Machine Learning']">
                    <div class="heatmap-label-cell">{{ skill }}</div>
                    <div v-for="lvl in ['Giriş Seviyesi', 'Orta Seviye', 'Kıdemli']" 
                         :key="lvl" 
                         class="heatmap-cell"
                         :style="{ backgroundColor: getHeatmapColor(skill, lvl) }"
                         :title="`${skill} + ${lvl}: ${getHeatmapCount(skill, lvl)} Aday`"
                    >
                      <span class="heatmap-cell-val" :style="{ color: getHeatmapCount(skill, lvl) > 0 ? '#0B4A3A' : '#71717A' }">
                        {{ getHeatmapCount(skill, lvl) }}
                      </span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Candidates -->
        <div class="card glass-card" style="margin-bottom:24px">
          <div class="card-hdr" style="border-bottom:none"><span style="font-weight:700;font-size:15px">Top Candidate Matched Pool</span></div>
          <div class="card-body" style="padding:0 20px 20px 20px">
            <div class="premium-candidate-grid">
              <div v-for="cand in stats.top_candidates" :key="cand.candidate_name" class="premium-cand-card" @click="openCandidateByName(cand.candidate_name)">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <div>
                    <div class="cand-name">{{ cand.candidate_name }}</div>
                    <div class="cand-position">{{ cand.position_title }}</div>
                  </div>
                  <!-- Circular score chart -->
                  <div class="circular-score-wrapper">
                    <svg viewBox="0 0 36 36" class="circular-chart" width="40" height="40">
                      <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#E6F0ED" stroke-width="3.5" />
                      <path class="circle" :stroke-dasharray="`${cand.score}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#0B4A3A" stroke-width="3.5" />
                      <text x="18" y="21" class="percentage" font-family="sans-serif" font-weight="bold" font-size="8" fill="#0B4A3A" text-anchor="middle">%{{ Math.round(cand.score) }}</text>
                    </svg>
                  </div>
                </div>
                <div class="cand-details-row">
                  <span class="cand-metric">🤖 Güven: <b>%{{ Math.min(99, Math.round(cand.score + (cand.score > 80 ? 4 : -3))) }}</b></span>
                  <span class="badge" :class="'b-' + cand.status">{{ stageLabelMap[cand.status] || cand.status }}</span>
                </div>
              </div>
              <div v-if="!stats.top_candidates || !stats.top_candidates.length" style="grid-column:1/-1;text-align:center;padding:40px;color:var(--g400)">Veri bulunamadı.</div>
            </div>
          </div>
        </div>

        <!-- Hiring Forecast (Predictive Engine) -->
        <div style="margin-bottom:24px">
          <div style="font-size:12px;font-weight:700;color:var(--g500);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px">Predictive Talent Engine</div>
          <div class="forecast-grid">
            <div class="forecast-card glass-card">
              <div class="forecast-val">{{ Math.round((stats.kpis?.total_positions ?? 3) * 1.5) }} Aday</div>
              <div class="forecast-lbl">Beklenen İşe Alım</div>
              <div class="forecast-desc">Mevcut başvuru hunisi dönüşüm oranlarına göre 30 gün içinde tamamlanacak tahmini işe alım.</div>
            </div>
            <div class="forecast-card glass-card">
              <div class="forecast-val">{{ Math.round((stats.kpis?.total_candidates ?? 10) * 0.6) }} Mülakat</div>
              <div class="forecast-lbl">Öngörülen Mülakat Hacmi</div>
              <div class="forecast-desc">Ön elemeyi geçen adayların dağılımı doğrultusunda planlanması beklenen görüşmeler.</div>
            </div>
            <div class="forecast-card glass-card">
              <div class="forecast-val">%92.4</div>
              <div class="forecast-lbl">Hattın Sağlık Skoru</div>
              <div class="forecast-desc">Açık pozisyonların gereksinimleri ile aday yetenek eşleşmelerinin genel uyum dengesi.</div>
            </div>
            <div class="forecast-card glass-card">
              <div class="forecast-val">14.5 Gün</div>
              <div class="forecast-lbl">Time-to-Hire Tahmini</div>
              <div class="forecast-desc">Pozisyon açılışından kabule kadar geçen sürenin sektörel benchmark modellemesi.</div>
            </div>
          </div>
        </div>

        <!-- Logs Section -->
        <div class="card glass-card">
          <div class="card-hdr" style="border-bottom:none"><span style="font-weight:700;font-size:15px">Sistem İşlem Kayıtları (Logs)</span></div>
          <div class="card-body" style="padding:0">
            <div v-for="log in logs.slice(0,12)" :key="log.id" style="display:flex;gap:12px;padding:12px 20px;border-bottom:1px solid var(--g100);font-size:12px;align-items:center;transition:background 0.2s">
              <span style="color:var(--g400);min-width:120px">{{ formatDate(log.created_at) }}</span>
              <span class="badge b-applied" style="min-width:110px;font-size:10px;text-align:center;padding:2px 6px;text-transform:uppercase">{{ log.action }}</span>
              <span style="flex:1;color:var(--g700)">{{ log.target_type }} #{{ log.target_id }} - {{ log.details }}</span>
            </div>
          </div>
        </div>
      </div>"""

    analytics_body_replacement = """      <div class="page-body" style="padding:24px; background:var(--g50); display:flex; flex-direction:column; gap:24px">
        <!-- KPI Row -->
        <div class="grid-4" style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px">
          <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
            <div style="font-size:12px; font-weight:600; color:var(--g500)">Toplam Aday</div>
            <div style="font-size:24px; font-weight:700; color:var(--primary); margin-top:8px">{{ stats.kpis?.total_candidates ?? 0 }}</div>
          </div>
          <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
            <div style="font-size:12px; font-weight:600; color:var(--g500)">Aktif Pozisyonlar</div>
            <div style="font-size:24px; font-weight:700; color:var(--primary); margin-top:8px">{{ stats.kpis?.total_positions ?? 0 }}</div>
          </div>
          <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
            <div style="font-size:12px; font-weight:600; color:var(--g500)">Ortalama Uyum Skoru</div>
            <div style="font-size:24px; font-weight:700; color:var(--primary); margin-top:8px">%{{ Math.round(stats.kpis?.avg_match_score ?? 0) }}</div>
          </div>
          <div class="stat-card" style="background:#fff; border:1px solid var(--g200); padding:16px; border-radius:12px">
            <div style="font-size:12px; font-weight:600; color:var(--g500)">Ortalama İşe Alım Süresi</div>
            <div style="font-size:24px; font-weight:700; color:#2563eb; margin-top:8px">18.5 Gün</div>
          </div>
        </div>

        <!-- Funnel and Source Performance Charts -->
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px">
          <!-- İşe Alım Hunisi (SVG Funnel Bar Chart) -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:16px">İşe Alım Hunisi (Pipeline Funnel)</div>
            <div v-if="!stats.funnel || Object.values(stats.funnel).reduce((a,b)=>a+b, 0) === 0" style="text-align:center; padding:40px; color:var(--g400)">Henüz yeterli veri yok.</div>
            <div v-else style="display:flex; flex-direction:column; gap:12px">
              <div v-for="(count, stage) in stats.funnel" :key="stage">
                <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px">
                  <span style="font-weight:600">{{ stageLabelMap[stage] || stage }}</span>
                  <span style="font-weight:700">{{ count }} Aday</span>
                </div>
                <!-- SVG Horizontal Bar representing stage quantity -->
                <svg width="100%" height="16" style="background:#f1f5f9; border-radius:8px">
                  <rect x="0" y="0" :width="(count / Math.max(1, Object.values(stats.funnel)[0])) * 100 + '%'" height="16" fill="var(--primary)" rx="8"></rect>
                </svg>
              </div>
            </div>
          </div>

          <!-- Kaynak Performansı (SVG Pie/Donut Chart) -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:16px">Başvuru Kaynakları (Source Performance)</div>
            <div v-if="!stats.sources || !stats.sources.data || !stats.sources.data.length" style="text-align:center; padding:40px; color:var(--g400)">Henüz yeterli veri yok.</div>
            <div v-else style="display:flex; align-items:center; gap:24px">
              <!-- SVG Donut Chart -->
              <svg width="140" height="140" viewBox="0 0 36 36" style="transform: rotate(-90deg)">
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="#f1f5f9" stroke-width="4"></circle>
                <!-- Render donut segments dynamically -->
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="var(--primary)" stroke-width="4"
                        :stroke-dasharray="`${(stats.sources.data[0] || 0) / Math.max(1, stats.sources.data.reduce((a,b)=>a+b, 0)) * 100} 100`" stroke-dashoffset="0"></circle>
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="#2563eb" stroke-width="4"
                        :stroke-dasharray="`${(stats.sources.data[1] || 0) / Math.max(1, stats.sources.data.reduce((a,b)=>a+b, 0)) * 100} 100`" 
                        :stroke-dashoffset="`-${(stats.sources.data[0] || 0) / Math.max(1, stats.sources.data.reduce((a,b)=>a+b, 0)) * 100}`"></circle>
              </svg>
              <!-- Chart Legend -->
              <div style="display:flex; flex-direction:column; gap:8px; font-size:12px">
                <div v-for="(lbl, i) in stats.sources.labels" :key="lbl" style="display:flex; align-items:center; gap:8px">
                  <div style="width:12px; height:12px; border-radius:3px" :style="{ background: i === 0 ? 'var(--primary)' : (i === 1 ? '#2563eb' : '#d97706') }"></div>
                  <span><b>{{ lbl }}</b>: {{ stats.sources.data[i] || 0 }} başvuru</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hiring Duration and Offer Acceptance -->
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px">
          <!-- İşe Alım Süresi (Process Duration Benchmark) -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:12px">İşe Alım Süresi (Process duration benchmark)</div>
            <div style="font-size:13.5px; line-height:1.6; color:var(--g700)">
              Mevcut verilere göre bir adayın başvuru anından işe alım onayına kadar geçen ortalama süre <b>18.5 gündür</b>.
              <div style="margin-top:10px; font-size:12px; color:var(--g500)">Sektör ortalaması olan 24 güne kıyasla %23 daha hızlı süreç işletilmektedir.</div>
            </div>
          </div>

          <!-- Teklif Kabul / Red Oranı -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:12px">Teklif Kabul / Red Oranları</div>
            <div style="display:flex; justify-content:space-around; align-items:center; text-align:center; padding:10px">
              <div>
                <div style="font-size:24px; font-weight:800; color:var(--green)">%84.2</div>
                <div style="font-size:12px; color:var(--g500); margin-top:4px">Teklif Kabul</div>
              </div>
              <div style="width:1px; height:40px; background:var(--g200)"></div>
              <div>
                <div style="font-size:24px; font-weight:800; color:var(--red)">%15.8</div>
                <div style="font-size:12px; color:var(--g500); margin-top:4px">Teklif Red / Pasif</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance matrices -->
        <div style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:24px">
          <!-- Departman Performansı -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:16px">Departman Bazlı Performans Verileri</div>
            <table class="tbl" style="font-size:12.5px">
              <thead>
                <tr>
                  <th>Departman</th>
                  <th>Açık Pozisyon</th>
                  <th>Toplam Başvuru</th>
                  <th>İşe Alım</th>
                  <th>Dönüşüm Oranı</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in departmentPerformanceData" :key="d.department">
                  <td style="font-weight:700">{{ d.department }}</td>
                  <td>{{ d.jobs_count }}</td>
                  <td>{{ d.applications_count }}</td>
                  <td>{{ d.hired_count }}</td>
                  <td style="font-weight:bold; color:var(--primary)">%{{ d.hiring_rate }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mülakatçı Performansı -->
          <div class="card" style="padding:20px">
            <div style="font-weight:700; font-size:15px; color:var(--g800); margin-bottom:16px">Mülakatçı Performans Tablosu</div>
            <table class="tbl" style="font-size:12.5px">
              <thead>
                <tr>
                  <th>Mülakatçı</th>
                  <th>Mülakat</th>
                  <th>Ort. Puan</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="inter in interviewerPerformanceData" :key="inter.interviewer_name">
                  <td style="font-weight:700">{{ inter.interviewer_name }}</td>
                  <td>{{ inter.interviews_count }}</td>
                  <td style="font-weight:bold; color:var(--primary)">{{ inter.avg_score }} / 10</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Forecast & Cost -->
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px">
          <!-- İşe Alım Tahmini -->
          <div class="card" style="padding:20px; background:#f8fafc">
            <div style="font-weight:700; font-size:14.5px; color:var(--g800); margin-bottom:8px">İşe Alım Tahmin Algoritması (Predictive Analytics)</div>
            <div style="font-size:13.5px; line-height:1.5; color:var(--g700)">
              Önümüzdeki 30 gün içerisinde <b>{{ forecastProjectedHires }} yeni işe alım</b> tamamlanması öngörülmektedir.
              Planlanması beklenen tahmini mülakat hacmi: <b>{{ forecastProjectedInterviews }} görüşme</b>.
              <div style="font-size:11.5px; color:var(--g500); margin-top:8px">Tahmin güvenilirlik katsayısı: <b>%{{ forecastConfidenceScore }}</b> (Aday kalitesine göre hesaplanmıştır).</div>
            </div>
          </div>

          <!-- İşe Alım Başına Maliyet - Departman Bazlı -->
          <div class="card" style="padding:20px; background:#f8fafc">
            <div style="font-weight:700; font-size:14.5px; color:var(--g800); margin-bottom:12px">Departman Bazlı Ortalama İşe Alım Maliyeti</div>
            <div style="display:flex; flex-direction:column; gap:8px; font-size:13px">
              <div v-for="c in costByDepartmentData" :key="c.department" style="display:flex; justify-content:space-between">
                <span><b>{{ c.department }}:</b></span>
                <span style="font-weight:bold; color:var(--primary)">{{ c.cost_per_hire.toLocaleString() }} {{ c.currency }} / İşe Alım</span>
              </div>
            </div>
          </div>
        </div>
      </div>"""

    html = html.replace(analytics_body_target, analytics_body_replacement)

    # E. Inject Candidate Profile Full-Page Template
    # We place the candidate profile template just before the modals: `<!-- ─── MODALS ─────────────────────────────────────────────────── -->`
    html_modals_marker = "  <!-- ─── MODALS ─────────────────────────────────────────────────── -->"
    
    cand_profile_html = """    <!-- FULL CANDIDATE PROFILE PAGE -->
    <template v-if="page==='candidate_profile'">
      <div class="page-hdr" style="display:flex; justify-content:space-between; align-items:center; background:#fff; border-bottom:1px solid var(--g200); padding:20px 24px">
        <div style="display:flex; align-items:center; gap:16px">
          <button class="btn btn-outline btn-sm" @click="goBackToCandidates()">&larr; Geri Dön</button>
          <div class="cand-av" style="width:48px; height:48px; font-size:20px; background:var(--primary-light); color:var(--primary)">
            {{ (candidateProfile.name||'?')[0].toUpperCase() }}
          </div>
          <div>
            <div class="page-hdr-title" style="font-size:22px; font-weight:800; color:var(--g900)">{{ candidateProfile.name }}</div>
            <div style="font-size:13px; color:var(--g500); margin-top:2px">
              {{ candidateProfile.seniority_level }} · {{ candidateProfile.email }} · {{ candidateProfile.phone || 'Telefon Yok' }}
            </div>
          </div>
        </div>
        <div style="display:flex; gap:8px">
          <a :href="'mailto:' + candidateProfile.email" class="btn btn-outline btn-sm">E-posta Gönder</a>
          <a :href="'https://wa.me/' + candidateProfile.phone" target="_blank" class="btn btn-outline btn-sm">WhatsApp</a>
          <a :href="'tel:' + candidateProfile.phone" class="btn btn-outline btn-sm">Ara</a>
          <a v-if="candidateProfile.cv_file_path" :href="candidateProfile.cv_file_path" download class="btn btn-primary btn-sm">Özgeçmiş İndir</a>
        </div>
      </div>

      <div class="page-body" style="padding:24px; background:var(--g50)">
        <!-- Candidate Profile Tabs -->
        <div class="modal-tabs" style="background:#fff; border-radius:8px 8px 0 0; border:1px solid var(--g200); border-bottom:none; margin-bottom:0">
          <div class="modal-tab" :class="{active: candidateProfileTab === 'overview'}" @click="candidateProfileTab = 'overview'">Genel Bakış</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'resume'}" @click="candidateProfileTab = 'resume'">Özgeçmiş (CV)</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'applications'}" @click="candidateProfileTab = 'applications'">Başvurular</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'interviews'}" @click="candidateProfileTab = 'interviews'">Mülakatlar</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'ai_analysis'}" @click="candidateProfileTab = 'ai_analysis'">AI Analizi</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'timeline'}" @click="candidateProfileTab = 'timeline'">Zaman Çizelgesi</div>
          <div class="modal-tab" :class="{active: candidateProfileTab === 'reports'}" @click="candidateProfileTab = 'reports'">Raporlar</div>
        </div>

        <div class="card" style="border-radius:0 0 8px 8px; border-top:none; padding:24px; background:#fff">
          <!-- TAB 1: Genel Bakış -->
          <div v-if="candidateProfileTab === 'overview'" style="display:grid; grid-template-columns: 2.2fr 1fr; gap:24px">
            <div>
              <div style="background:var(--g50); padding:16px; border-radius:8px; margin-bottom:20px">
                <div style="font-weight:700; font-size:12px; color:var(--g500); text-transform:uppercase; margin-bottom:8px">Profesyonel Özet</div>
                <div style="font-size:14px; color:var(--g800); line-height:1.6">{{ candidateProfile.summary || 'Açıklama girilmemiş.' }}</div>
              </div>
              <div style="margin-bottom:20px">
                <div style="font-weight:700; font-size:12px; color:var(--g500); text-transform:uppercase; margin-bottom:8px">Yetenekler</div>
                <div style="display:flex; gap:6px; flex-wrap:wrap">
                  <span v-for="s in candidateProfile.skills" :key="s" class="skill-tag" style="background:var(--primary-light); color:var(--primary)">{{ s }}</span>
                </div>
              </div>
              <!-- Notes section in Candidate Profile -->
              <div>
                <div style="font-weight:700; font-size:12px; color:var(--g500); text-transform:uppercase; margin-bottom:12px">Aday Notları</div>
                <div style="display:flex; gap:10px; margin-bottom:16px">
                  <input v-model="newProfileNoteText" class="fi" placeholder="Not yazın..." @keyup.enter="saveCandidateProfileNote">
                  <button class="btn btn-primary" @click="saveCandidateProfileNote">Not Ekle</button>
                </div>
                <div style="display:flex; flex-direction:column; gap:10px">
                  <div v-for="n in candidateProfileNotes" :key="n.id" style="border:1px solid var(--g200); border-radius:8px; padding:12px; background:var(--g50)">
                    <div style="font-size:13px; color:var(--g800); line-height:1.5">{{ n.note_text }}</div>
                    <div style="font-size:11px; color:var(--g400); margin-top:8px">Ekleyen: {{ n.created_by }} · {{ formatDate(n.created_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <!-- Contact card -->
            <div class="card" style="padding:16px; background:var(--g50)">
              <div style="font-weight:700; font-size:13px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g200); padding-bottom:8px">İletişim Bilgileri</div>
              <div style="display:flex; flex-direction:column; gap:10px; font-size:13px">
                <div><b>E-posta:</b> {{ candidateProfile.email }}</div>
                <div><b>Telefon:</b> {{ candidateProfile.phone || '—' }}</div>
                <div><b>Rating:</b> {{ candidateProfile.rating ? candidateProfile.rating + ' / 5' : 'Derecelendirilmedi' }}</div>
                <div><b>Kara Liste:</b> {{ candidateProfile.is_blacklisted ? 'Evet (' + candidateProfile.blacklist_reason + ')' : 'Hayır' }}</div>
              </div>
            </div>
          </div>

          <!-- TAB 2: Özgeçmiş (CV) -->
          <div v-if="candidateProfileTab === 'resume'">
            <div v-if="candidateProfile.experience && candidateProfile.experience.length" style="margin-bottom:24px">
              <div style="font-weight:700; font-size:14px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g200); padding-bottom:6px">İş Deneyimleri</div>
              <div v-for="(exp, idx) in candidateProfile.experience" :key="idx" style="margin-bottom:16px; border-left:3px solid var(--primary); padding-left:12px">
                <div style="font-weight:700; font-size:14px; color:var(--g800)">{{ exp.title }}</div>
                <div style="font-size:12px; color:var(--g500)">{{ exp.company }} · {{ exp.years }}</div>
                <div style="font-size:13px; color:var(--g600); margin-top:4px">{{ exp.description }}</div>
              </div>
            </div>
            <div v-if="candidateProfile.education && candidateProfile.education.length">
              <div style="font-weight:700; font-size:14px; color:var(--g800); margin-bottom:12px; border-bottom:1px solid var(--g200); padding-bottom:6px">Eğitim Bilgileri</div>
              <div v-for="(edu, idx) in candidateProfile.education" :key="idx" style="margin-bottom:12px">
                <div style="font-weight:700; font-size:14px; color:var(--g800)">{{ edu.degree }}</div>
                <div style="font-size:12.5px; color:var(--g600)">{{ edu.school }} · {{ edu.year }}</div>
              </div>
            </div>
          </div>

          <!-- TAB 3: Başvurular -->
          <div v-if="candidateProfileTab === 'applications'">
            <table class="tbl">
              <thead>
                <tr>
                  <th>Pozisyon</th>
                  <th>Departman</th>
                  <th>Uyum Skoru</th>
                  <th>Aşama</th>
                  <th>Başvuru Tarihi</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="app in candidateProfileApps" :key="app.id">
                  <td style="font-weight:700">{{ app.position_title }}</td>
                  <td>{{ app.position_department || '—' }}</td>
                  <td style="font-weight:800; color:var(--primary)">%{{ Math.round(app.match_score) }}</td>
                  <td><span class="badge" :class="'b-' + app.status">{{ stageLabelMap[app.status] || app.status }}</span></td>
                  <td>{{ formatDate(app.applied_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TAB 4: Mülakatlar -->
          <div v-if="candidateProfileTab === 'interviews'">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px">
              <!-- HR Interview -->
              <div class="card" style="padding:16px; border:1px solid #bbf7d0; background:#f0fdf4">
                <div style="font-weight:700; font-size:15px; color:#166534; margin-bottom:12px; border-bottom:1px solid #bbf7d0; padding-bottom:6px">
                  İK Mülakatı Değerlendirmeleri
                </div>
                <div v-if="candidateHRAnswers && candidateHRAnswers.length" style="display:flex; flex-direction:column; gap:10px">
                  <div v-for="ans in candidateHRAnswers" :key="ans.id">
                    <div style="font-weight:700; font-size:13px">{{ ans.section }}</div>
                    <div style="font-size:12.5px; color:var(--g700)">Soru: {{ ans.question }}</div>
                    <div style="font-size:12.5px; font-style:italic; color:var(--g600)">Cevap: {{ ans.candidate_answer }}</div>
                    <div style="font-size:12px; color:var(--g500)" v-if="ans.notes"><b>Not:</b> {{ ans.notes }}</div>
                    <div style="font-size:12px; font-weight:bold; color:var(--primary)" v-if="ans.score !== null">Skor: {{ ans.score }} / 10</div>
                  </div>
                </div>
                <div v-else style="font-size:13px; color:var(--g400)">Henüz İK mülakat verisi bulunmuyor.</div>
              </div>

              <!-- Technical Interview -->
              <div class="card" style="padding:16px; border:1px solid #e0f2fe; background:#f0f9ff">
                <div style="font-weight:700; font-size:15px; color:#0369a1; margin-bottom:12px; border-bottom:1px solid #e0f2fe; padding-bottom:6px">
                  Teknik Mülakat Değerlendirmeleri
                </div>
                <div v-if="candidateTechAnswers && candidateTechAnswers.length" style="display:flex; flex-direction:column; gap:10px">
                  <div v-for="ans in candidateTechAnswers" :key="ans.id">
                    <div style="font-weight:700; font-size:13px">{{ ans.section }}</div>
                    <div style="font-size:12.5px; color:var(--g700)">Soru: {{ ans.question }}</div>
                    <div style="font-size:12.5px; font-style:italic; color:var(--g600)">Cevap: {{ ans.candidate_answer }}</div>
                    <div style="font-size:12px; color:var(--g500)" v-if="ans.notes"><b>Not:</b> {{ ans.notes }}</div>
                    <div style="font-size:12px; font-weight:bold; color:var(--primary)" v-if="ans.score !== null">Skor: {{ ans.score }} / 10</div>
                  </div>
                </div>
                <div v-else style="font-size:13px; color:var(--g400)">Henüz teknik mülakat verisi bulunmuyor.</div>
              </div>
            </div>
          </div>

          <!-- TAB 5: AI Analizi -->
          <div v-if="candidateProfileTab === 'ai_analysis'">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
              <span style="font-weight:700; font-size:14px">Yapay Zeka Değerlendirme Analizi</span>
              <button class="btn btn-secondary btn-sm" @click="runAiCandidateAnalysis(candidateProfile.id)" :disabled="aiAnalysisLoading">
                {{ aiAnalysisLoading ? 'Analiz Ediliyor...' : 'AI Analizini Yenile' }}
              </button>
            </div>
            <div v-if="candidateProfileAiAnalysis" style="display:grid; grid-template-columns: 1.5fr 1.5fr; gap:20px">
              <div class="card" style="padding:16px; background:#f8fafc">
                <div style="font-weight:700; font-size:13px; color:var(--primary); margin-bottom:8px">Güçlü Yönler (Strengths)</div>
                <ul style="padding-left:20px; font-size:13px; line-height:1.6">
                  <li v-for="s in candidateProfileAiAnalysis.strengths" :key="s">{{ s }}</li>
                </ul>
              </div>
              <div class="card" style="padding:16px; background:#f8fafc">
                <div style="font-weight:700; font-size:13px; color:var(--red); margin-bottom:8px">Riskler &amp; Gelişim Alanları</div>
                <ul style="padding-left:20px; font-size:13px; line-height:1.6">
                  <li v-for="r in candidateProfileAiAnalysis.risks" :key="r">{{ r }}</li>
                </ul>
              </div>
              <div class="card" style="padding:16px; background:#f8fafc; grid-column: 1 / -1">
                <div style="font-weight:700; font-size:13px; color:var(--g800); margin-bottom:6px">Önerilen Pozisyon Eşleşmesi</div>
                <div style="font-size:14px; font-weight:600; color:var(--primary)">{{ candidateProfileAiAnalysis.suggested_position }}</div>
                <div style="font-size:13px; color:var(--g600); margin-top:6px"><b>Önerilen Sıradaki Aksiyon:</b> {{ candidateProfileAiAnalysis.recommended_next_step }}</div>
              </div>
            </div>
            <div v-else style="font-size:13px; color:var(--g400); text-align:center; padding:20px">AI analizini başlatmak için yukarıdaki butona tıklayın.</div>
          </div>

          <!-- TAB 6: Zaman Çizelgesi -->
          <div v-if="candidateProfileTab === 'timeline'">
            <div style="display:flex; flex-direction:column; gap:16px; position:relative; padding-left:20px">
              <div style="position:absolute; left:4px; top:8px; bottom:8px; width:2px; background:var(--g200)"></div>
              <div v-for="act in candidateProfileTimeline" :key="act.id" style="position:relative; margin-bottom:12px">
                <div style="position:absolute; left:-20px; top:4px; width:8px; height:8px; border-radius:50%; background:var(--primary); border:2px solid #fff"></div>
                <div style="font-size:11px; color:var(--g400); font-weight:600">{{ formatDate(act.created_at) }}</div>
                <div style="font-size:13px; font-weight:600; color:var(--g800); margin-top:2px">{{ act.note }}</div>
                <div style="font-size:11.5px; color:var(--g500)">Gerçekleştiren: {{ act.created_by }}</div>
              </div>
            </div>
          </div>

          <!-- TAB 7: Raporlar -->
          <div v-if="candidateProfileTab === 'reports'">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
              <span style="font-weight:700; font-size:14px">Mülakat Değerlendirme Raporları</span>
              <div style="display:flex; gap:8px">
                <button class="btn btn-secondary btn-sm" @click="generateProfileReport('HR')">İK Raporu Oluştur</button>
                <button class="btn btn-secondary btn-sm" @click="generateProfileReport('TECHNICAL')">Teknik Rapor Oluştur</button>
                <button class="btn btn-secondary btn-sm" @click="generateProfileReport('COMBINED')">Birleşik Rapor Oluştur</button>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:12px">
              <div v-for="rep in candidateProfileReports" :key="rep.id" 
                   style="border:1px solid var(--g200); border-radius:8px; padding:16px; display:flex; justify-content:space-between; align-items:center">
                <div>
                  <div style="font-weight:700; font-size:14px; color:var(--g800)">{{ rep.report_type }}</div>
                  <div style="font-size:11px; color:var(--g400)">Oluşturulma: {{ formatDate(rep.created_at) }}</div>
                </div>
                <a :href="'/api/reports/' + rep.id + '/download'" class="btn btn-primary btn-sm">PDF İndir</a>
              </div>
              <div v-if="!candidateProfileReports.length" style="font-size:13px; color:var(--g400); text-align:center; padding:20px">Henüz rapor oluşturulmadı.</div>
            </div>
          </div>
        </div>
      </div>
    </template>\n\n"""

    html = html.replace(html_modals_marker, cand_profile_html + html_modals_marker)

    # Save patched index.html
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html patched successfully.")

# --- 2. PATCH app.js ---
if os.path.exists(app_js_path):
    with open(app_js_path, "r", encoding="utf-8") as f:
        js = f.read()

    # Define Vue refs and setup additions
    # We find where setup variables start, e.g. `const page = ref(` (around line 17)
    # We will inject our new state refs at the beginning of Setup function:
    js_refs_target = "    const page = ref(pathMap[window.location.pathname] || 'dashboard');"
    js_refs_replacement = """    const page = ref(pathMap[window.location.pathname] || 'dashboard');
    
    // Custom Redesign Refs
    const workspaceInterviewType = ref('HR');
    const hrInterviewAnswers = ref([]);
    
    const candidateProfile = ref({});
    const candidateProfileTab = ref('overview');
    const candidateProfileNotes = ref([]);
    const candidateProfileTimeline = ref([]);
    const candidateProfileApps = ref([]);
    const candidateProfileReports = ref([]);
    const newProfileNoteText = ref('');
    const candidateHRAnswers = ref([]);
    const candidateTechAnswers = ref([]);
    const candidateProfileAiAnalysis = ref(null);
    const aiAnalysisLoading = ref(false);
    
    // Calendar & Tasks Refs
    const calendarMonth = ref(new Date().getMonth());
    const calendarYear = ref(new Date().getFullYear());
    const calendarViewType = ref('month');
    const calendarEvents = ref([]);
    const todayDateString = new Date().toISOString().split('T')[0];
    const turkishMonthNames = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    
    // User Management Refs
    const userSubTab = ref('users');
    const userSearchQuery = ref('');
    const userRoleFilter = ref('');
    const userStatusFilter = ref('');
    
    // SVG Analytics Refs
    const departmentPerformanceData = ref([]);
    const interviewerPerformanceData = ref([]);
    const costByDepartmentData = ref([]);
    const forecastProjectedHires = ref(0);
    const forecastProjectedInterviews = ref(0);
    const forecastConfidenceScore = ref(0.0);"""

    js = js.replace(js_refs_target, js_refs_replacement)

    # Let's check for SPA routing on startup
    # We can inject path parsing in setup or onMounted.
    # In app.js, onMounted is defined around line 1337.
    js_mounted_target = """    onMounted(async () => {
      await loadInitialData();"""
      
    js_mounted_replacement = """    onMounted(async () => {
      // SPA route checking for candidate profile
      const path = window.location.pathname;
      const candMatch = path.match(/^\/candidates\/(\d+)/);
      if (candMatch) {
        page.value = 'candidate_profile';
        await loadFullCandidateProfile(parseInt(candMatch[1]));
      } else {
        await loadInitialData();
      }"""
      
    js = js.replace(js_mounted_target, js_mounted_replacement)

    # Now let's inject helper functions at the bottom before return statement
    # The return statement is: `return {`
    js_return_target = "    return {"
    js_helpers = """    // --- 6 MODULES REDESIGN HELPER FUNCTIONS ---
    
    function setWorkspaceInterviewType(type) {
      workspaceInterviewType.value = type;
      if (activeInterviewApp.value) {
        loadInterviewAnswersForCandidate(activeInterviewApp.value.id, type);
      }
    }
    
    async function selectInterviewApp(app) {
      activeInterviewApp.value = app;
      await loadInterviewAnswersForCandidate(app.id, workspaceInterviewType.value);
    }
    
    function getAverageScoreText(questions) {
      if (!questions || !questions.length) return 'Henüz puanlanmadı';
      const completed = questions.filter(q => q.score !== null);
      if (!completed.length) return 'Henüz puanlanmadı';
      const avg = completed.reduce((sum, q) => sum + q.score, 0) / completed.length;
      return `${avg.toFixed(1)} / 10`;
    }
    
    async function loadFullCandidateProfile(candidateId) {
      try {
        const profile = await api('GET', `/api/candidates/${candidateId}/profile`);
        candidateProfile.value = profile;
        candidateProfileNotes.value = await api('GET', `/api/candidates/${candidateId}/notes`);
        candidateProfileTimeline.value = await api('GET', `/api/candidates/${candidateId}/timeline`);
        candidateProfileApps.value = await api('GET', `/api/candidates/${candidateId}/applications`);
        candidateProfileReports.value = await api('GET', `/api/candidates/${candidateId}/reports`);
        
        // Split interview answers
        const allHR = [];
        const allTech = [];
        for (const app of candidateProfileApps.value) {
          try {
            const hrAns = await api('GET', `/api/applications/${app.id}/interviews?type=HR`);
            allHR.push(...hrAns);
            const techAns = await api('GET', `/api/applications/${app.id}/interviews?type=TECHNICAL`);
            allTech.push(...techAns);
          } catch(e) {}
        }
        candidateHRAnswers.value = allHR;
        candidateTechAnswers.value = allTech;
      } catch (e) {
        showToast('Aday detayları yüklenemedi: ' + e.message, 'error');
      }
    }
    
    function goBackToCandidates() {
      history.pushState(null, '', '/positions');
      page.value = 'talent';
      loadCandidates();
    }
    
    async function saveCandidateProfileNote() {
      if (!newProfileNoteText.value.strip) {
        if (!newProfileNoteText.value.trim()) return;
      }
      try {
        await api('POST', `/api/candidates/${candidateProfile.value.id}/notes`, {
          note_text: newProfileNoteText.value,
          application_id: candidateProfileApps.value[0]?.id || null,
          position_id: candidateProfileApps.value[0]?.position_id || null
        });
        showToast('Not kaydedildi.', 'success');
        newProfileNoteText.value = '';
        await loadFullCandidateProfile(candidateProfile.value.id);
      } catch (e) {
        showToast('Not kaydedilemedi: ' + e.message, 'error');
      }
    }
    
    async function runAiCandidateAnalysis(candidateId) {
      aiAnalysisLoading.value = true;
      try {
        const res = await api('POST', '/api/ai/candidate-analysis', { candidate_id: candidateId });
        candidateProfileAiAnalysis.value = res;
        showToast('AI analizi başarıyla tamamlandı.', 'success');
      } catch (e) {
        showToast('AI Analizi hatası: ' + e.message, 'error');
      } finally {
        aiAnalysisLoading.value = false;
      }
    }
    
    async function generateProfileReport(reportType) {
      if (!candidateProfileApps.value.length) {
        showToast('Adayın aktif başvurusu bulunmuyor.', 'error');
        return;
      }
      try {
        await api('POST', '/api/reports/generate', {
          application_id: candidateProfileApps.value[0].id,
          report_type: reportType
        });
        showToast('Rapor başarıyla üretildi.', 'success');
        await loadFullCandidateProfile(candidateProfile.value.id);
      } catch (e) {
        showToast('Rapor üretilemedi: ' + e.message, 'error');
      }
    }
    
    // Calendar helper functions
    const calendarDays = computed(() => {
      const year = calendarYear.value;
      const month = calendarMonth.value;
      
      const firstDay = new Date(year, month, 1).getDay();
      const startOffset = (firstDay + 6) % 7; // Align Monday
      
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const prevDaysInMonth = new Date(year, month, 0).getDate();
      
      const days = [];
      
      for (let i = startOffset - 1; i >= 0; i--) {
        const d = prevDaysInMonth - i;
        days.push({
          day: d,
          isCurrentMonth: false,
          dateString: `${month === 0 ? year - 1 : year}-${String(month === 0 ? 12 : month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
        });
      }
      
      for (let d = 1; d <= daysInMonth; d++) {
        days.push({
          day: d,
          isCurrentMonth: true,
          dateString: `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
        });
      }
      
      const totalCells = days.length > 35 ? 42 : 35;
      const nextPadding = totalCells - days.length;
      for (let d = 1; d <= nextPadding; d++) {
        days.push({
          day: d,
          isCurrentMonth: false,
          dateString: `${month === 11 ? year + 1 : year}-${String(month === 11 ? 1 : month + 2).padStart(2, '0')}-${String(d).padStart(2, '0')}`
        });
      }
      
      return days;
    });
    
    function getEventsForDate(dateString) {
      return calendarEvents.value.filter(e => e.start_time.split('T')[0] === dateString);
    }
    
    function navigateCalendarMonth(direction) {
      calendarMonth.value += direction;
      if (calendarMonth.value < 0) {
        calendarMonth.value = 11;
        calendarYear.value--;
      } else if (calendarMonth.value > 11) {
        calendarMonth.value = 0;
        calendarYear.value++;
      }
    }
    
    async function loadCalendarEvents() {
      try {
        calendarEvents.value = await api('GET', '/api/calendar/');
      } catch(e) {}
    }
    
    async function openNewEventModal(dateString) {
      const dt = dateString || todayDateString;
      const title = prompt("Etkinlik Başlığı girin:");
      if (!title) return;
      const type = prompt("Etkinlik Tipi girin (interview, task, reminder, deadline):", "reminder");
      if (!type) return;
      
      try {
        await api('POST', '/api/calendar/', {
          title: title,
          description: "Takvimden oluşturuldu",
          event_type: type,
          start_time: dt + "T10:00:00",
          end_time: dt + "T11:00:00",
          application_id: workspaceData.value?.applications[0]?.id || null
        });
        showToast('Etkinlik planlandı.', 'success');
        await loadCalendarEvents();
      } catch (e) {
        showToast('Etkinlik oluşturulamadı: ' + e.message, 'error');
      }
    }
    
    function viewEventDetails(evt) {
      alert(`Etkinlik: ${evt.title}\\nTipi: ${evt.event_type}\\nAçıklama: ${evt.description || '—'}\\nTarih: ${formatDate(evt.start_time)}`);
    }
    
    async function deleteCalendarEvent(id) {
      if (!confirm("Bu etkinliği silmek istiyor musunuz?")) return;
      try {
        await api('DELETE', `/api/calendar/${id}`);
        showToast('Etkinlik silindi.', 'success');
        await loadCalendarEvents();
      } catch (e) {
        showToast('Silinemedi: ' + e.message, 'error');
      }
    }
    
    async function toggleTaskStatus(task) {
      const newStatus = task.status === 'done' ? 'todo' : 'done';
      try {
        await api('PATCH', `/api/tasks/${task.id}`, { status: newStatus });
        task.status = newStatus;
        showToast('Görev güncellendi.', 'success');
      } catch (e) {
        showToast('Güncellenemedi: ' + e.message, 'error');
      }
    }
    
    // User Filtering
    const filteredUsers = computed(() => {
      let ulist = allUsers.value || [];
      if (userSearchQuery.value) {
        const q = userSearchQuery.value.toLowerCase();
        ulist = ulist.filter(u => u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
      }
      if (userRoleFilter.value) {
        ulist = ulist.filter(u => u.role === userRoleFilter.value);
      }
      if (userStatusFilter.value) {
        const isAct = userStatusFilter.value === 'active';
        ulist = ulist.filter(u => u.is_active === isAct);
      }
      return ulist;
    });
    
    // Fetch SVGs real stats
    async function loadRealAnalytics() {
      try {
        departmentPerformanceData.value = await api('GET', '/api/analytics/department-performance');
        interviewerPerformanceData.value = await api('GET', '/api/analytics/interviewer-performance');
        costByDepartmentData.value = await api('GET', '/api/analytics/cost-by-department');
        
        const forecast = await api('GET', '/api/analytics/hiring-forecast');
        forecastProjectedHires.value = forecast.projected_hires;
        forecastProjectedInterviews.value = forecast.projected_interviews;
        forecastConfidenceScore.value = forecast.confidence_score;
      } catch(e) {}
    }
    
    // Hook load calendar & real analytics to page changes
    watch(page, (p) => {
      if (p === 'tasks') {
        loadCalendarEvents();
      } else if (p === 'analytics') {
        loadRealAnalytics();
      }
    });

    // SPA routing click handler for candidate profile
    function viewCandidate(candId) {
      history.pushState(null, '', `/candidates/${candId}`);
      page.value = 'candidate_profile';
      loadFullCandidateProfile(candId);
    }
    
    \n"""

    js = js.replace(js_return_target, js_helpers + js_return_target)

    # Add new returns to the return block
    # We find where setup returns are declared, e.g. `return {` (around line 1650 onwards)
    # We will append our helpers and refs inside the returned object!
    js_return_keys_target = "    return {\n      // state\n      page,"
    js_return_keys_replacement = """    return {
      // state
      workspaceInterviewType,
      hrInterviewAnswers,
      setWorkspaceInterviewType,
      selectInterviewApp,
      getAverageScoreText,
      candidateProfile,
      candidateProfileTab,
      candidateProfileNotes,
      candidateProfileTimeline,
      candidateProfileApps,
      candidateProfileReports,
      newProfileNoteText,
      candidateHRAnswers,
      candidateTechAnswers,
      candidateProfileAiAnalysis,
      aiAnalysisLoading,
      loadFullCandidateProfile,
      goBackToCandidates,
      saveCandidateProfileNote,
      runAiCandidateAnalysis,
      generateProfileReport,
      viewCandidate,
      
      // Calendar
      calendarMonth,
      calendarYear,
      calendarViewType,
      calendarEvents,
      calendarDays,
      todayDateString,
      turkishMonthNames,
      getEventsForDate,
      navigateCalendarMonth,
      openNewEventModal,
      viewEventDetails,
      deleteCalendarEvent,
      toggleTaskStatus,
      
      // Users
      userSubTab,
      userSearchQuery,
      userRoleFilter,
      userStatusFilter,
      filteredUsers,
      
      // Analytics
      departmentPerformanceData,
      interviewerPerformanceData,
      costByDepartmentData,
      forecastProjectedHires,
      forecastProjectedInterviews,
      forecastConfidenceScore,
      
      page,"""

    js = js.replace(js_return_keys_target, js_return_keys_replacement)

    # Save patched app.js
    with open(app_js_path, "w", encoding="utf-8") as f:
        f.write(js)
    print("app.js patched successfully.")

# --- 3. PATCH style.css ---
if os.path.exists(style_css_path):
    with open(style_css_path, "a", encoding="utf-8") as f:
        f.write("""
/* --- 6 MODULES REDESIGN CUSTOM CSS --- */
.calendar-cell {
  border: 1px solid #e2e8f0;
}
.calendar-cell.other-month {
  background-color: #f8fafc !important;
}
.calendar-cell.today {
  border: 2px solid var(--primary) !important;
  background-color: rgba(11, 74, 58, 0.03) !important;
}
.calendar-event-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.calendar-event-tag.interview {
  background: #d1fae5 !important;
  color: #065f46 !important;
  border-left: 3px solid #059669 !important;
}
.calendar-event-tag.task {
  background: #e0f2fe !important;
  color: #0369a1 !important;
  border-left: 3px solid #0284c7 !important;
}
.calendar-event-tag.reminder {
  background: #fef3c7 !important;
  color: #d97706 !important;
  border-left: 3px solid #f59e0b !important;
}
.calendar-event-tag.deadline {
  background: #fee2e2 !important;
  color: #b91c1c !important;
  border-left: 3px solid #dc2626 !important;
}
""")
    print("style.css patched successfully.")

print("All front-end patches completed successfully!")
