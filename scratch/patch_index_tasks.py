index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

start_tag = '<template v-if="page===\'tasks\'">'
end_tag = '</template>'

start_idx = html.find(start_tag)
end_idx = html.find(end_tag, start_idx + len(start_tag))

if start_idx != -1 and end_idx != -1:
    before = html[:start_idx]
    after = html[end_idx:]
    
    tasks_html = """<template v-if="page==='tasks'">
      <div class="page-hdr">
        <div>
          <div class="page-hdr-title">Tasks & Calendar</div>
          <div class="page-hdr-sub">Schedule interviews and track recruiter tasks</div>
        </div>
        <div style="margin-left:auto; display:flex; gap:12px; align-items:center;">
          <div class="search-bar" style="height:36px; display:flex; align-items:center; gap:8px; background:var(--g100); border-radius:12px; padding:0 12px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="candidateSearch" placeholder="Search candidates, positions..." style="border:none; background:transparent; outline:none; font-size:12.5px; width:100%;">
          </div>
          <button class="btn btn-ghost" style="padding:8px; position:relative; background:transparent; border:none; cursor:pointer;" @click="alert('No notifications')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>
            <span style="position:absolute; top:4px; right:4px; width:8px; height:8px; background:var(--danger); border-radius:50%;"></span>
          </button>
          <button class="btn btn-primary btn-sm" @click="showNewDropdown = !showNewDropdown" style="height:36px; border-radius:12px; display:flex; align-items:center; gap:4px;">+ New</button>
        </div>
      </div>

      <div class="page-body">
        <div style="display:grid; grid-template-columns:2.2fr 1fr; gap:24px;">
          <!-- Left Column: Calendar & Day Event Details -->
          <div style="display:flex; flex-direction:column; gap:24px;">
            <!-- Monthly Calendar Card -->
            <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div style="display:flex; align-items:center; gap:12px;">
                  <button class="btn btn-secondary btn-sm" style="padding:6px; border-radius:8px;" @click="alert('Previous Month')">&lt;</button>
                  <span style="font-weight:700; font-size:16px; color:var(--text-primary);">June 2024</span>
                  <button class="btn btn-secondary btn-sm" style="padding:6px; border-radius:8px;" @click="alert('Next Month')">&gt;</button>
                </div>
                <div style="display:flex; gap:8px;">
                  <div style="background:var(--g100); border-radius:8px; padding:3px; display:flex; gap:2px;">
                    <button class="btn btn-secondary btn-sm" style="border:none; padding:4px 10px; border-radius:6px; background:#FFF; box-shadow:var(--sh); font-weight:600; font-size:12px;">Month</button>
                    <button class="btn btn-ghost btn-sm" style="padding:4px 10px; border-radius:6px; font-weight:500; font-size:12px;" @click="alert('Week view')">Week</button>
                  </div>
                  <button class="btn btn-primary btn-sm" style="border-radius:8px;" @click="showNewInterviewModal=true">+ Add Event</button>
                </div>
              </div>

              <!-- Days Grid Header -->
              <div style="display:grid; grid-template-columns:repeat(7, 1fr); text-align:center; font-weight:700; font-size:12px; color:var(--text-secondary); margin-bottom:12px; border-bottom:1px solid var(--border); padding-bottom:8px;">
                <div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div><div>SUN</div>
              </div>

              <!-- Calendar Days Grid -->
              <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px;">
                <div v-for="day in calendarDays" :key="day.dateStr"
                     style="background: #FFF; border: 1px solid var(--border); border-radius: 12px; min-height: 90px; padding: 8px; display: flex; flex-direction: column; justify-content: space-between;"
                     :style="[
                       day.isCurrentMonth ? '' : 'opacity: 0.4; background: var(--bg);',
                       day.dayNum === 14 && day.isCurrentMonth ? 'border: 2px solid var(--primary);' : ''
                     ]">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight: 800; font-size: 13px;" :style="day.dayNum === 14 && day.isCurrentMonth ? 'background:var(--primary); color:#FFF; width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center;' : ''">{{ day.dayNum }}</span>
                  </div>

                  <!-- Events inside calendar cell -->
                  <div style="margin-top:6px; display:flex; flex-direction:column; gap:4px; max-height:50px; overflow-y:auto;">
                    <!-- June 14 HR Interview Event -->
                    <div v-if="day.dayNum === 14 && day.isCurrentMonth" class="badge b-interview" style="font-size: 9.5px; padding: 2px 6px; border-left: 3px solid var(--primary); display:block; white-space:nowrap; text-overflow:ellipsis; overflow:hidden; background:var(--primary-light); color:var(--primary); font-weight:600;">
                      10:00 HR Interview - Ayşe Kaya
                    </div>
                    <!-- June 15 Technical Interview Event -->
                    <div v-if="day.dayNum === 15 && day.isCurrentMonth" class="badge b-applied" style="font-size: 9.5px; padding: 2px 6px; border-left: 3px solid var(--blue); display:block; white-space:nowrap; text-overflow:ellipsis; overflow:hidden; background:#E0F2FE; color:#0369A1; font-weight:600;">
                      14:00 Technical Interview - Priya
                    </div>
                    <!-- Other database events -->
                    <div v-for="iv in interviews.filter(item => item.interview_date === day.dateStr && day.dayNum !== 14 && day.dayNum !== 15)" :key="iv.id"
                         class="badge b-interview" style="font-size: 9px; padding: 2px 4px; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; display: block; border-left: 3px solid var(--primary);">
                      {{ iv.interview_time }} {{ iv.candidate_name }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Event Details Panel -->
            <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
              <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px; border-bottom:1px solid var(--border); padding-bottom:8px;">June 14, 2024</div>
              <div style="display:flex; align-items:flex-start; gap:16px;">
                <div style="font-size:13px; font-weight:600; color:var(--text-secondary); width:80px; text-align:right;">
                  <div style="font-size:16px; font-weight:700; color:var(--text-primary);">10:00</div>
                  <div>60 min</div>
                </div>
                <div style="flex:1; background:var(--bg); padding:16px; border-radius:12px; border:1px solid var(--border); border-left:4px solid var(--primary);">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <div>
                      <span class="badge b-interview" style="font-size:10px; font-weight:700;">HR Interview</span>
                      <h4 style="font-size:15px; font-weight:700; color:var(--text-primary); margin-top:4px;">HR Interview - Ayşe Kaya</h4>
                    </div>
                  </div>
                  <div style="font-size:13px; color:var(--text-secondary); display:flex; flex-direction:column; gap:6px;">
                    <div>👤 <b>Candidate:</b> Ayşe Kaya (Director of Revenue Management)</div>
                    <div>📍 <b>Location:</b> Meeting Room A</div>
                    <div>👥 <b>Interviewers:</b> James Okonkwo, Sarah Mitchell</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Tasks Panel & Upcoming Interviews -->
          <div style="display:flex; flex-direction:column; gap:24px;">
            <!-- Tasks Panel -->
            <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh); display:flex; flex-direction:column;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <span style="font-weight:700; font-size:15px; color:var(--text-primary);">Tasks</span>
                <button class="btn btn-primary btn-sm" style="border-radius:8px;" @click="openNewTaskModal">+ New Task</button>
              </div>
              <div style="display:flex; flex-direction:column; gap:12px;">
                <!-- Task 1 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Review 3 new CVs - Spa Director</div>
                      <div style="font-size:11px; color:var(--danger); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--danger); border-radius:50%;"></span> Today
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Task 2 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Schedule technical interview - Sophie</div>
                      <div style="font-size:11px; color:var(--danger); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--danger); border-radius:50%;"></span> Today
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Task 3 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border); opacity:0.75;">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" checked style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary); text-decoration:line-through;">Send rejection to Carlos Rivera</div>
                      <div style="font-size:11px; color:var(--success); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--success); border-radius:50%;"></span> Today
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Task 4 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Update position JD - IT Lead</div>
                      <div style="font-size:11px; color:var(--warning); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--warning); border-radius:50%;"></span> Jun 16
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Task 5 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Prepare offer letter template - Elena</div>
                      <div style="font-size:11px; color:var(--danger); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--danger); border-radius:50%;"></span> Jun 18
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Task 6 -->
                <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" style="width:16px; height:16px; accent-color:var(--primary);">
                    <div>
                      <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Monthly recruitment report for CHRO</div>
                      <div style="font-size:11px; color:var(--text-secondary); display:flex; align-items:center; gap:4px;">
                        <span style="width:6px; height:6px; background:var(--text-secondary); border-radius:50%;"></span> Jun 30
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Upcoming Interviews Panel -->
            <div class="card" style="border-radius:16px; background:#FFF; border:1px solid var(--border); padding:24px; box-shadow:var(--sh);">
              <div style="font-weight:700; font-size:15px; color:var(--text-primary); margin-bottom:16px;">Upcoming Interviews</div>
              <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="padding:10px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Ayşe Kaya</div>
                  <div style="font-size:11px; color:var(--text-secondary);">HR Interview</div>
                  <div style="font-size:11px; color:var(--primary); font-weight:600; margin-top:4px;">Jun 14 @ 10:00</div>
                </div>
                <div style="padding:10px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Priya Sharma</div>
                  <div style="font-size:11px; color:var(--text-secondary);">Technical Interview</div>
                  <div style="font-size:11px; color:var(--primary); font-weight:600; margin-top:4px;">Jun 15 @ 14:00</div>
                </div>
                <div style="padding:10px; background:var(--bg); border-radius:12px; border:1px solid var(--border);">
                  <div style="font-size:13px; font-weight:600; color:var(--text-primary);">Elena Volkov</div>
                  <div style="font-size:11px; color:var(--text-secondary);">Panel Interview</div>
                  <div style="font-size:11px; color:var(--primary); font-weight:600; margin-top:4px;">Jun 17 @ 11:00</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>"""
    
    html = before + tasks_html + after
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Tasks & Calendar page patched successfully!")
else:
    print("Tasks page template block indices not resolved properly.")
