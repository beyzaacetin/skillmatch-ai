const { createApp, ref, computed, onMounted, nextTick, watch } = Vue;

createApp({
  setup() {
    // ─── STATE ───────────────────────────────────────────────────────
    const pathMap = {
      '/': 'dashboard',
      '/candidates': 'talent',
      '/pipeline': 'pipeline',
      '/analytics': 'analytics',
      '/positions': 'jobs',
      '/interviews': 'interviews',
      '/tasks': 'tasks',
      '/ai_search': 'ai_search',
      '/users': 'users'
    };
    const page = ref(pathMap[window.location.pathname] || 'dashboard');
    
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
    const forecastConfidenceScore = ref(0.0);
    const currentUser = ref(JSON.parse(localStorage.getItem('user') || 'null'));
    const token = ref(localStorage.getItem('token') || '');
    const talentView = ref('list');
    const candidates = ref([]);
    const positions = ref([]);
    const stats = ref({});
    const pipeline = ref([]);
    const pipelineLoading = ref(false);
    const pipelinePositionFilter = ref('');
    const allInterviews = ref([]);
    const pipelineStats = ref({});

    // AI Interview Assistant State
    const interviewTab = ref('list');
    const ivAssistant = ref({ candidateId: '', positionId: '', loading: false, questions: [] });
    const ivAnalysis = ref({ interviewId: '', rawNotes: '', loading: false, result: null });

    // Toast system
    const toasts = ref([]);
    function showToast(msg, type = 'info') {
      const id = Date.now();
      toasts.value.push({ id, message: msg, type });
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id);
      }, 4500);
    }
    // Intercept default window alert
    window.alert = (msg) => {
      let type = 'info';
      const lower = msg.toLowerCase();
      if (lower.includes('hata') || lower.includes('başarısız') || lower.includes('silinemedi') || lower.includes('dikkat') || lower.includes('hata oluştu')) {
        type = 'error';
      } else if (lower.includes('başarıyla') || lower.includes('güncellendi') || lower.includes('eklendi') || lower.includes('kaydedildi')) {
        type = 'success';
      }
      showToast(msg, type);
    };

    // Match Details Modal State
    const showMatchDetails = ref(false);
    const currentMatchScore = ref(null);
    const matchScoreLoading = ref(false);

    async function viewMatchDetails(app) {
      showMatchDetails.value = true;
      matchScoreLoading.value = true;
      currentMatchScore.value = null;
      try {
        const ms = await api('GET', `/api/applications/${app.id}/match-score`);
        currentMatchScore.value = ms;
      } catch (e) {
        showToast('Eşleşme detayı yüklenemedi: ' + e.message, 'error');
      }
      matchScoreLoading.value = false;
    }

    // Filters
    const candidateSearch = ref('');
    const talentFilter = ref({ seniority: '', sort: 'newest', showInactive: false });
    const logs = ref([]);
    const recommendedPositions = ref([]);
    const analyticsPositionFilter = ref('');
    const analyticsDateFilter = ref('30d');

    // Selected items
    const selectedCandidate = ref(null);
    const candidateTab = ref('overview');
    const candidateNote = ref('');
    const candidateApps = ref([]);
    const selectedPosition = ref(null);
    const posTab = ref('overview');
    const positionApps = ref([]);
    const positionMatches = ref([]);
    const posMatchLoading = ref(false);
    const selectedMatchCandidates = ref([]);
    const posUploads = ref([]);
    const deepAiResults = ref([]);
    const deepAiLoading = ref(false);
    const selectedApp = ref(null);
    const appTab = ref('overview');
    const appNotes = ref('');
    const appInterviews = ref([]);
    const currentOffer = ref(null);
    const onboardingTasks = ref([]);
    const showAllQ = ref(false);

    // Modals
    const showUpload = ref(false);
    const showNewPositionModal = ref(false);
    const showNewAppModal = ref(false);
    const showNewInterviewModal = ref(false);
    const showNewOfferModal = ref(false);

    // Match modal
    const matchModal = ref({ show: false, candidate: null, positionId: '', results: [], loading: false });

    // Forms
    const newPos = ref({ title: '', department: '', description: '', seniority_level: '', required_skills_str: '', salary_min: null, salary_max: null });
    const newApp = ref({ candidate_id: '', position_id: '', source: '', cover_letter: '' });
    const newIv = ref({ round_number: 1, interview_type: 'hr', scheduled_at: '', duration_minutes: 60, interviewer_name: '', meeting_link: '' });
    const newOffer = ref({ proposed_salary: null, start_date: '', position_title: '', benefits_str: '', notes: '' });
    const loginData = ref({ email: '', password: '' });
    const authMode = ref('login');
    const registerData = ref({ full_name: '', email: '', password: '', department: '' });
    const allUsers = ref([]);

    // AI Search, Tasks, Bulk, Timeline, Users CRUD State
    const aiSearchQuery = ref('');
    const aiSearchResults = ref([]);
    const aiSearchLoading = ref(false);
    const aiSearchSearched = ref(false);
    const aiSearchStats = ref('');
    const recruitmentTasks = ref([]);
    const selectedTask = ref(null);
    const showTaskModal = ref(false);
    const newTask = ref({ title: '', description: '', status: 'todo', assigned_to: '', due_date: '' });
    const selectedApplicationIds = ref([]);
    const selectedCandidateIds = ref([]);
    const selectedCandidates = computed(() =>
      candidates.value.filter(c => selectedCandidateIds.value.includes(c.id))
    );
    const showBulkActionModal = ref(false);
    const bulkActionType = ref('');
    const bulkActionValue = ref('');
    const candidateTimeline = ref([]);
    const showNewUserModal = ref(false);
    const showEditUserModal = ref(false);
    const showPasswordResetModal = ref(false);
    const newUser = ref({ full_name: '', email: '', password: '', department: '', role: 'RECRUITER', is_active: true });
    const editingUser = ref(null);
    const passwordResetData = ref({ userId: null, password: '', confirmPassword: '' });

    // Interview feedback
    const feedbackIv = ref(null);
    const ivFeedback = ref({ overall_score: null, technical_score: null, cultural_score: null, notes: '', recommendation: '', strengths_str: '', concerns_str: '' });

    // Upload
    const uploadQueue = ref([]);
    const dragover = ref(false);

    // Drag & drop
    const draggedApp = ref(null);
    const dragOverCol = ref(null);

    // Chat
    const chatOpen = ref(false);
    const chatInput = ref('');
    const chatMessages = ref([{ id: 0, role: 'bot', text: 'Merhaba! Ben SkillMatch AI İK Asistanınım. Adaylar, pozisyonlar veya işe alım süreci hakkında sorularınızı yanıtlayabilirim.' }]);
    const chatLoading = ref(false);
    const chatMsgs = ref(null);

    // Analytics
    const analyticsStats = ref({});
    const topSkills = ref({});

    // ─── CONSTANTS ───────────────────────────────────────────────────
    const stages = [
      { value: 'applied', label: 'Başvurdu' },
      { value: 'screening', label: 'Değerlendirme' },
      { value: 'hr_interview', label: 'İK Mülakatı' },
      { value: 'tech_interview', label: 'Teknik Mülakat' },
      { value: 'manager_interview', label: 'Yönetici Mülakatı' },
      { value: 'reference_check', label: 'Referans Kontrolü' },
      { value: 'offer', label: 'Teklif' },
      { value: 'hired', label: 'İşe Alındı' },
      { value: 'rejected', label: 'Elendi' },
      { value: 'hold', label: 'Beklemede' },
    ];

    const stageLabelMap = {
      applied: 'Başvurdu',
      screening: 'Değerlendirme',
      hr_interview: 'İK Mülakatı',
      tech_interview: 'Teknik Mülakat',
      manager_interview: 'Yönetici Mülakatı',
      reference_check: 'Referans Kontrolü',
      offer: 'Teklif',
      hired: 'İşe Alındı',
      rejected: 'Elendi',
      hold: 'Beklemede'
    };

    // ─── COMPUTED ─────────────────────────────────────────────────────
    const filteredCandidates = computed(() => {
      let list = candidates.value;
      const q = candidateSearch.value.toLowerCase();
      if (q) list = list.filter(c =>
        (c.name || '').toLowerCase().includes(q) ||
        (c.skills || []).some(s => s.toLowerCase().includes(q)) ||
        (c.summary || '').toLowerCase().includes(q)
      );
      if (talentFilter.value.seniority)
        list = list.filter(c => c.seniority_level === talentFilter.value.seniority);
      
      // Filter out hired/rejected unless showInactive is true
      if (!talentFilter.value.showInactive) {
        // Adayın mülakat süreci bitmişse (Hired/Rejected) listeden düşür
        // Not: Bu bilgi applications üzerinden geldiği için biraz karmaşık olabilir.
        // Şimdilik sadece blacklisted olanları da filtreleyebiliriz.
        list = list.filter(c => !c.is_blacklisted);
      }

      const sort = talentFilter.value.sort;
      if (sort === 'name') list = [...list].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
      else if (sort === 'rating') list = [...list].sort((a, b) => (b.rating || 0) - (a.rating || 0));
      else if (sort === 'score') list = [...list].sort((a, b) => (b.seniority_score || 0) - (a.seniority_score || 0));
      else list = [...list].sort((a, b) => b.id - a.id);

      return list;
    });

    // ─── API HELPERS ──────────────────────────────────────────────────
    async function api(method, url, body = null) {
      const headers = { 'Content-Type': 'application/json' };
      if (token.value) headers['Authorization'] = `Bearer ${token.value}`;
      const opts = { method, headers };
      if (body) opts.body = JSON.stringify(body);
      const r = await fetch(url, opts);
      if (r.status === 401 && !url.includes('/api/auth/login')) { logout(); throw new Error('Oturum süresi doldu'); }
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      if (r.status === 204) return null;
      return r.json();
    }

    async function apiForm(url, formData) {
      const r = await fetch(url, { method: 'POST', body: formData });
      if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
      return r.json();
    }

    // ─── AUTH ────────────────────────────────────────────────────────
    async function login() {
      try {
        const res = await api('POST', '/api/auth/login', loginData.value);
        currentUser.value = res.user;
        token.value = res.access_token;
        localStorage.setItem('user', JSON.stringify(res.user));
        localStorage.setItem('token', res.access_token);
        loadInitialData();
      } catch (e) { alert('Giriş başarısız: ' + e.message); }
    }

    async function register() {
      try {
        await api('POST', '/api/auth/register', registerData.value);
        alert('Kaydınız başarıyla oluşturuldu. Şimdi giriş yapabilirsiniz.');
        authMode.value = 'login';
        loginData.value.email = registerData.value.email;
        registerData.value = { full_name: '', email: '', password: '', department: '' };
      } catch (e) { alert('Kayıt başarısız: ' + e.message); }
    }

    function logout() {
      currentUser.value = null;
      token.value = '';
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }

    // ─── LOAD DATA ────────────────────────────────────────────────────
    async function loadInitialData() {
      if (!currentUser.value) return;
      await Promise.all([loadCandidates(), loadPositions(), loadAnalytics()]);
    }

    async function loadCandidates() {
      candidates.value = await api('GET', '/api/candidates/with-best-position');
    }

    async function loadPositions() {
      positions.value = await api('GET', '/api/positions/');
    }

    async function loadAnalytics() {
      try {
        const posFilter = analyticsPositionFilter.value ? `&position_id=${analyticsPositionFilter.value}` : '';
        const dateFilter = analyticsDateFilter.value ? `&date_range=${analyticsDateFilter.value}` : '';
        const [data, logsData] = await Promise.all([
          api('GET', `/api/analytics/stats?${posFilter}${dateFilter}`),
          api('GET', '/api/analytics/logs')
        ]);
        stats.value = data;
        logs.value = logsData;
        // Build topSkills from chart data
        if (data.charts?.skills) {
          const sk = {};
          (data.charts.skills.labels || []).forEach((lbl, i) => {
            sk[lbl] = data.charts.skills.data[i] || 0;
          });
          topSkills.value = sk;
        }
        // Build analyticsStats
        analyticsStats.value = {
          candidates: { value: data.kpis?.total_candidates ?? data.total_candidates, label: 'Toplam Aday' },
          positions: { value: data.kpis?.total_positions ?? data.total_positions, label: 'Aktif Pozisyon' },
          matchRate: { value: data.kpis?.avg_match_score ? `%${data.kpis.avg_match_score}` : (data.performance?.match_accuracy || '—'), label: 'Ortalama Uyum Skoru' },
          avgTime: { value: data.kpis?.total_applications ?? '—', label: 'Toplam Başvuru' },
        };
      } catch (e) { console.error(e); }
    }

    async function loadPipeline() {
      pipelineLoading.value = true;
      try {
        const url = pipelinePositionFilter.value
          ? `/api/applications/pipeline?position_id=${pipelinePositionFilter.value}`
          : '/api/applications/pipeline';
        const data = await api('GET', url);
        pipeline.value = data.columns || [];
        // Build stats
        const ps = {};
        (data.columns || []).forEach(col => { ps[col.status] = col.count; });
        pipelineStats.value = ps;
      } catch (e) { console.error(e); }
      pipelineLoading.value = false;
    }

    async function loadAllInterviews() {
      try {
        // Load from all applications
        const apps = await api('GET', '/api/applications/');
        const ivs = [];
        for (const app of apps.slice(0, 30)) {
          try {
            const appIvs = await api('GET', `/api/interviews/application/${app.id}`);
            appIvs.forEach(iv => {
              iv.candidate_name = app.candidate?.name;
              iv.position_title = app.position?.title;
              ivs.push(iv);
            });
          } catch (e) {}
        }
        allInterviews.value = ivs;
      } catch (e) { console.error(e); }
    }

    // ─── USER MANAGEMENT (YETKİ ALANI) ────────────────────────────────
    async function loadUsers() {
      try {
        allUsers.value = await api('GET', '/api/users/');
      } catch (e) { console.error(e); }
    }

    function openNewUserModal() {
      newUser.value = { full_name: '', email: '', password: '', department: '', role: 'RECRUITER', is_active: true };
      showNewUserModal.value = true;
    }

    async function saveNewUser() {
      try {
        const res = await api('POST', '/api/users/', newUser.value);
        allUsers.value.push(res);
        showNewUserModal.value = false;
        alert('Kullanıcı başarıyla oluşturuldu.');
      } catch (e) { alert('Kullanıcı eklenemedi: ' + e.message); }
    }

    async function toggleUserStatus(user, active) {
      try {
        const endpoint = active ? `/api/users/${user.id}/activate` : `/api/users/${user.id}/deactivate`;
        const res = await api('PUT', endpoint);
        user.is_active = res.is_active;
        alert(active ? 'Kullanıcı başarıyla aktifleştirildi.' : 'Kullanıcı başarıyla pasifleştirildi.');
      } catch (e) { alert('Hata: ' + e.message); }
    }

    function editUser(user) {
      editingUser.value = { ...user, password: '' };
      showEditUserModal.value = true;
    }

    async function updateUser() {
      try {
        const payload = { ...editingUser.value };
        if (!payload.password || payload.password.trim() === '') {
          delete payload.password;
        }
        const res = await api('PUT', `/api/users/${editingUser.value.id}`, payload);
        const idx = allUsers.value.findIndex(u => u.id === res.id);
        if (idx >= 0) allUsers.value[idx] = res;
        showEditUserModal.value = false;
        alert('Kullanıcı başarıyla güncellendi.');
      } catch (e) { alert('Hata: ' + e.message); }
    }

    function openPasswordReset(user) {
      passwordResetData.value = { userId: user.id, password: '', confirmPassword: '' };
      showPasswordResetModal.value = true;
    }

    async function submitPasswordReset() {
      if (passwordResetData.value.password !== passwordResetData.value.confirmPassword) {
        alert('Şifreler eşleşmiyor!');
        return;
      }
      try {
        await api('PUT', `/api/users/${passwordResetData.value.userId}/reset-password`, { password: passwordResetData.value.password });
        showPasswordResetModal.value = false;
        alert('Kullanıcı şifresi başarıyla yenilendi.');
      } catch (e) { alert('Hata: ' + e.message); }
    }

    // ─── AI TALENT SEARCH ─────────────────────────────────────────────
    async function runAiTalentSearch() {
      if (!aiSearchQuery.value.trim()) return;
      aiSearchLoading.value = true;
      aiSearchResults.value = [];
      aiSearchSearched.value = true;
      aiSearchStats.value = 'Arama yapılıyor...';
      try {
        const res = await api('POST', '/api/ai/talent-search', { query: aiSearchQuery.value });
        aiSearchResults.value = res.results || [];
        aiSearchStats.value = `Filtreler uygulandı: ${res.query_understanding || 'Yapay Zeka Araması'}. ${res.results?.length || 0} aday bulundu.`;
      } catch (e) {
        alert('Arama başarısız: ' + e.message);
        aiSearchStats.value = 'Hata oluştu.';
      }
      aiSearchLoading.value = false;
    }

    async function viewCandidateById(id) {
      try {
        const cand = await api('GET', `/api/candidates/${id}`);
        openCandidate(cand);
        page.value = 'talent';
      } catch (e) {
        alert('Aday detayı yüklenemedi: ' + e.message);
      }
    }

    // ─── RECRUITMENT TASKS & CALENDAR (KANBAN) ────────────────────────
    async function loadRecruitmentTasks() {
      try {
        recruitmentTasks.value = await api('GET', '/api/tasks/');
      } catch (e) { console.error(e); }
    }

    function openNewTaskModal() {
      selectedTask.value = null;
      newTask.value = { title: '', description: '', status: 'todo', assigned_to: '', due_date: '' };
      showTaskModal.value = true;
    }

    async function saveRecruitmentTask() {
      try {
        if (selectedTask.value) {
          const res = await api('PUT', `/api/tasks/${selectedTask.value.id}`, newTask.value);
          const idx = recruitmentTasks.value.findIndex(t => t.id === res.id);
          if (idx >= 0) recruitmentTasks.value[idx] = res;
        } else {
          const res = await api('POST', '/api/tasks/', newTask.value);
          recruitmentTasks.value.push(res);
        }
        showTaskModal.value = false;
        alert('Görev başarıyla kaydedildi.');
      } catch (e) { alert('Hata: ' + e.message); }
    }

    function editRecruitmentTask(task) {
      selectedTask.value = task;
      newTask.value = { ...task };
      showTaskModal.value = true;
    }

    async function deleteRecruitmentTask() {
      if (!selectedTask.value) return;
      if (!confirm('Bu görevi silmek istediğinize emin misiniz?')) return;
      try {
        await api('DELETE', `/api/tasks/${selectedTask.value.id}`);
        recruitmentTasks.value = recruitmentTasks.value.filter(t => t.id !== selectedTask.value.id);
        showTaskModal.value = false;
        alert('Görev silindi.');
      } catch (e) { alert('Hata: ' + e.message); }
    }

    // ─── CANDIDATE TIMELINE ───────────────────────────────────────────
    async function loadCandidateTimeline(candidateId) {
      try {
        candidateTimeline.value = await api('GET', `/api/candidates/${candidateId}/activities`);
      } catch (e) {
        candidateTimeline.value = [];
      }
    }

    // ─── BULK PIPELINE ACTIONS ────────────────────────────────────────
    async function submitBulkAction(action, value = '') {
      let appIds = [];
      if (page.value === 'talent') {
        const apps = await api('GET', '/api/applications/');
        const candIds = selectedCandidateIds.value;
        appIds = apps.filter(a => candIds.includes(a.candidate_id)).map(a => a.id);
      } else if (page.value === 'pipeline') {
        appIds = [...selectedApplicationIds.value];
      }

      if (!appIds.length) {
        alert('Lütfen işlem yapmak istediğiniz adayları/başvuruları seçin.');
        return;
      }

      const note = prompt('İşlem için not ekleyin (isteğe bağlı):', 'Toplu işlem gerçekleştirildi.');
      if (note === null) return; // cancelled

      try {
        const payload = {
          application_ids: appIds,
          action: action,
          stage: action === 'change_stage' ? value : undefined,
          tag: action === 'add_tag' ? value : undefined,
          note: note
        };
        await api('POST', '/api/applications/bulk-update', payload);
        alert('Toplu işlem başarıyla tamamlandı.');
        selectedCandidateIds.value = [];
        selectedApplicationIds.value = [];
        loadInitialData();
        if (page.value === 'pipeline') loadPipeline();
      } catch (e) {
        alert('Toplu işlem hatası: ' + e.message);
      }
    }

    // ─── CANDIDATE COMMUNICATION MODULE ────────────────────────────────
    const showCommModal = ref(false);
    const commCandidate = ref(null);
    const commChannel = ref('whatsapp'); // 'whatsapp' or 'email'
    const commMsgType = ref('first_contact');
    const commTone = ref('professional');
    const commText = ref('');
    const commSubject = ref('');
    const commLoading = ref(false);
    const commPositionId = ref('');

    const isViewer = computed(() => currentUser.value?.role?.toUpperCase() === 'VIEWER');

    function normalizePhoneForWhatsApp(phone) {
      if (!phone) return null;
      let cleaned = phone.replace(/[\s\(\)\-\+]/g, '');
      if (!cleaned) return null;
      if (cleaned.startsWith('0')) {
        cleaned = '90' + cleaned.substring(1);
      } else if (cleaned.length === 10) {
        cleaned = '90' + cleaned;
      }
      return cleaned;
    }

    function openCommunication(candidate, channel = 'whatsapp') {
      const userRole = currentUser.value?.role?.toUpperCase();
      if (userRole === 'VIEWER') {
        showToast('İzleyici (Viewer) rolü aday iletişim özelliklerini kullanamaz.', 'error');
        return;
      }
      commCandidate.value = candidate;
      commChannel.value = channel;
      commMsgType.value = channel === 'whatsapp' ? 'first_contact' : 'application_received';
      commTone.value = channel === 'whatsapp' ? 'professional' : 'professional';
      commText.value = '';
      commSubject.value = '';
      commPositionId.value = '';
      showCommModal.value = true;
    }

    async function generateAiDraft() {
      if (!commCandidate.value) return;
      commLoading.value = true;
      try {
        if (commChannel.value === 'whatsapp') {
          const payload = {
            candidate_id: commCandidate.value.id,
            position_id: commPositionId.value ? parseInt(commPositionId.value) : null,
            message_type: commMsgType.value,
            tone: commTone.value
          };
          const res = await api('POST', '/api/ai/whatsapp-draft', payload);
          commText.value = res.message;
        } else {
          const payload = {
            candidate_id: commCandidate.value.id,
            position_id: commPositionId.value ? parseInt(commPositionId.value) : null,
            email_type: commMsgType.value,
            tone: commTone.value
          };
          const res = await api('POST', '/api/ai/email-draft', payload);
          commSubject.value = res.subject;
          commText.value = res.body;
        }
      } catch (e) {
        showToast('Taslak oluşturulamadı: ' + e.message, 'error');
      } finally {
        commLoading.value = false;
      }
    }

    async function logCommActivity(activityType, note) {
      if (!commCandidate.value) return;
      try {
        await api('POST', `/api/candidates/${commCandidate.value.id}/activity`, {
          activity_type: activityType,
          note: note,
          metadata_json: { channel: commChannel.value }
        });
        loadCandidateTimeline(commCandidate.value.id);
      } catch (e) {
        console.error('Failed to log activity:', e);
      }
    }

    async function openInExternalChannel() {
      if (!commCandidate.value) return;
      if (commChannel.value === 'whatsapp') {
        const phone = normalizePhoneForWhatsApp(commCandidate.value.phone);
        if (!phone) {
          alert('Geçerli bir telefon numarası bulunamadı.');
          return;
        }
        let url = `https://wa.me/${phone}`;
        if (commText.value) {
          url += `?text=${encodeURIComponent(commText.value)}`;
        }
        window.open(url, '_blank');
        await logCommActivity('whatsapp_opened', 'Aday ile WhatsApp üzerinden iletişim başlatıldı.');
      } else {
        const email = commCandidate.value.email;
        if (!email) {
          alert('E-posta adresi bulunamadı.');
          return;
        }
        let mailto = `mailto:${email}`;
        let params = [];
        if (commSubject.value) params.push(`subject=${encodeURIComponent(commSubject.value)}`);
        if (commText.value) params.push(`body=${encodeURIComponent(commText.value)}`);
        if (params.length) mailto += `?${params.join('&')}`;
        window.open(mailto, '_self');
        await logCommActivity('email_opened', `Adaya e-posta taslağı açıldı: ${commSubject.value || 'Konu Yok'}`);
      }
    }

    async function copyCommText() {
      try {
        let textToCopy = commText.value;
        if (commChannel.value === 'email' && commSubject.value) {
          textToCopy = `Konu: ${commSubject.value}\n\n${commText.value}`;
        }
        await navigator.clipboard.writeText(textToCopy);
        showToast('Metin panoya kopyalandı.', 'success');
        await logCommActivity('message_copied', `Taslak metin panoya kopyalandı (${commChannel.value}).`);
      } catch (err) {
        showToast('Kopyalama başarısız oldu.', 'error');
      }
    }

    function getDaysSinceLastActivity(candidate, timeline) {
      if (!candidate) return 0;
      let lastDate = null;
      if (timeline && timeline.length > 0) {
        const latest = timeline[0];
        if (latest.created_at) {
          lastDate = new Date(latest.created_at);
        }
      }
      if (!lastDate && candidate.created_at) {
        lastDate = new Date(candidate.created_at);
      }
      if (!lastDate) return 0;
      const diffTime = Math.abs(new Date() - lastDate);
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    }


    // ─── CANDIDATES ───────────────────────────────────────────────────
    function openCandidate(c) {
      selectedCandidate.value = c;
      candidateTab.value = 'overview';
      candidateNote.value = c.notes || '';
      loadRecommendedPositions(c);
      loadCandidateTimeline(c.id);
    }

    async function loadRecommendedPositions(c) {
      try {
        // Simple logic: get all positions and show top 3 based on match score
        // In real app, we might have a dedicated endpoint
        const posList = await api('GET', '/api/positions/');
        const scored = [];
        for (const p of posList.slice(0, 5)) {
          const res = await api('GET', `/api/positions/${p.id}/matches`);
          const match = res.find(m => m.candidate.id === c.id);
          if (match) scored.push({ ...p, score: match.score });
        }
        recommendedPositions.value = scored.sort((a,b) => b.score - a.score).slice(0,3);
      } catch (e) { recommendedPositions.value = []; }
    }

    async function toggleBlacklist(c) {
      const reason = c.is_blacklisted ? null : prompt('Kara listeye alma sebebi:', 'Uygun olmayan davranış');
      if (!c.is_blacklisted && reason === null) return;
      try {
        const res = await api('PATCH', `/api/candidates/${c.id}/blacklist`, { reason });
        c.is_blacklisted = res.is_blacklisted;
        c.blacklist_reason = res.reason;
        if (c.is_blacklisted) alert('Aday kara listeye alındı.');
      } catch (e) { alert('Hata oluştu'); }
    }

    async function rateCandidate(c, rating) {
      try {
        await api('PATCH', `/api/candidates/${c.id}/rating`, { rating });
        c.rating = rating;
      } catch (e) { alert('Rating kaydedilemedi'); }
    }

    async function saveNote(c) {
      try {
        await api('PATCH', `/api/candidates/${c.id}/notes`, { notes: candidateNote.value });
        c.notes = candidateNote.value;
      } catch (e) { alert('Not kaydedilemedi'); }
    }

    async function deleteCandidate(id) {
      if (!confirm('Bu adayı silmek istediğinize emin misiniz?')) return;
      try {
        await api('DELETE', `/api/candidates/${id}`);
        candidates.value = candidates.value.filter(c => c.id !== id);
        if (selectedCandidate.value?.id === id) selectedCandidate.value = null;
      } catch (e) { alert('Silinemedi: ' + e.message); }
    }

    async function loadCandidateApps(candidateId) {
      try {
        const apps = await api('GET', `/api/applications/?candidate_id=${candidateId}`);
        candidateApps.value = apps;
      } catch (e) { candidateApps.value = []; }
    }

    function openMatchModal(c) {
      matchModal.value = { show: true, candidate: c, positionId: '', results: [], loading: false };
      selectedCandidate.value = null;
    }

    async function runMatch() {
      if (!matchModal.value.positionId) return;
      matchModal.value.loading = true;
      try {
        const results = await api('GET', `/api/positions/${matchModal.value.positionId}/matches`);
        matchModal.value.results = results;
      } catch (e) { alert('Eşleştirme hatası: ' + e.message); }
      matchModal.value.loading = false;
    }

    // ─── POSITIONS ────────────────────────────────────────────────────
    async function aiGeneratePosition() {
      if (!newPos.value.title) return;
      try {
        const data = await api('POST', '/api/positions/analyze', { title: newPos.value.title });
        newPos.value.description = data.description || newPos.value.description;
        newPos.value.required_skills_str = (data.skills || []).join(', ');
        if (data.salary) {
          newPos.value.salary_min = data.salary.min;
          newPos.value.salary_max = data.salary.max;
        }
      } catch (e) { alert('AI öneri alınamadı'); }
    }

    async function savePosition() {
      try {
        const payload = {
          ...newPos.value,
          required_skills: newPos.value.required_skills_str.split(',').map(s => s.trim()).filter(Boolean),
          preferred_skills: [],
        };
        delete payload.required_skills_str;
        const saved = await api('POST', '/api/positions/', payload);
        positions.value.unshift(saved);
        showNewPositionModal.value = false;
        newPos.value = { title: '', department: '', description: '', seniority_level: '', required_skills_str: '', salary_min: null, salary_max: null };
      } catch (e) { alert('Kayıt hatası: ' + e.message); }
    }

    async function deletePosition(id) {
      if (!confirm('Bu pozisyonu silmek istediğinize emin misiniz?')) return;
      try {
        await api('DELETE', `/api/positions/${id}`);
        positions.value = positions.value.filter(p => p.id !== id);
      } catch (e) { alert('Silinemedi: ' + e.message); }
    }

    async function openMatchPosition(p) {
      matchModal.value = { show: true, candidate: null, positionId: p.id, results: [], loading: true };
      await runMatch();
    }

    async function openPositionDetail(p) {
      selectedPosition.value = p;
      posTab.value = 'overview';
      posUploads.value = [];
      await loadWorkspace(p.id);
    }

    async function loadPositionApps(p) {
      try {
        positionApps.value = await api('GET', `/api/applications/?position_id=${p.id}`);
      } catch (e) { positionApps.value = []; }
    }

    async function loadPositionMatches(p) {
      posMatchLoading.value = true;
      selectedMatchCandidates.value = [];
      try {
        positionMatches.value = await api('GET', `/api/positions/${p.id}/matches`);
      } catch (e) { positionMatches.value = []; }
      posMatchLoading.value = false;
    }

    async function bulkAddCandidatesToPosition() {
      if (!selectedMatchCandidates.value.length || !selectedPosition.value) return;
      const pId = selectedPosition.value.id;
      let added = 0;
      for (const cid of selectedMatchCandidates.value) {
        const c = candidates.value.find(cand => cand.id === cid);
        if (c && c.is_blacklisted) continue;
        try {
          await api('POST', '/api/applications/', { candidate_id: cid, position_id: pId, source: 'Toplu Ekleme', cover_letter: '' });
          added++;
        } catch(e) {}
      }
      alert(`${added} aday pozisyona eklendi.`);
      selectedMatchCandidates.value = [];
      posTab.value = 'candidates';
      loadPositionApps(selectedPosition.value);
      loadPipeline();
    }

    async function runDeepAIAnalysis() {
      if (!selectedPosition.value) return;
      deepAiLoading.value = true;
      try {
        const topIds = positionApps.value.map(app => app.candidate.id);
        
        if (topIds.length === 0) {
          alert('Bu pozisyona eklenmiş aday bulunamadı. Lütfen önce pozisyona aday ekleyin.');
          deepAiLoading.value = false;
          return;
        }

        const res = await api('POST', `/api/positions/${selectedPosition.value.id}/deep-analyze`, { candidate_ids: topIds });
        deepAiResults.value = res.results.sort((a,b) => a.rank - b.rank);
      } catch(e) {
        alert("Derin AI Analizi sırasında hata: " + e.message);
      }
      deepAiLoading.value = false;
    }

    function getCandidateForDeepAI(id) {
      return candidates.value.find(c => c.id === id) || {};
    }

    function handlePositionCvDrop(e) {
      if(e.dataTransfer.files) Array.from(e.dataTransfer.files).forEach(f => posUploads.value.push({ file: f, status: 'pending' }));
    }
    function handlePositionCvSelect(e) {
      if(e.target.files) Array.from(e.target.files).forEach(f => posUploads.value.push({ file: f, status: 'pending' }));
    }
    async function startPositionUploads() {
      for (const u of posUploads.value) {
        if (u.status !== 'pending' && u.status !== 'error') continue;
        u.status = 'uploading';
        try {
          const fd = new FormData();
          fd.append('file', u.file);
          const tk = localStorage.getItem('sm_token');
          const opts = { method: 'POST', body: fd, headers: {} };
          if(tk) opts.headers['Authorization'] = 'Bearer ' + tk;
          const res = await fetch('/api/candidates/upload', opts);
          const data = await res.json();
          if(!res.ok) throw new Error(data.detail||'Hata');
          
          await api('POST', '/api/applications/', {
            candidate_id: data.id,
            position_id: selectedPosition.value.id,
            source: 'Pozisyona CV Yükleme',
            cover_letter: ''
          });
          u.status = 'done';
        } catch(e) {
          u.status = 'error';
          u.error = e.message;
        }
      }
      loadCandidates();
      loadPositionApps(selectedPosition.value);
    }

    // ─── PIPELINE / APPLICATIONS ──────────────────────────────────────
    function openAppDetail(app) {
      selectedApp.value = app;
      appTab.value = 'overview';
      appNotes.value = app.hr_notes || '';
    }

    function openNewAppForStage(status) {
      showNewAppModal.value = true;
    }

    async function saveNewApp() {
      if (!newApp.value.candidate_id || !newApp.value.position_id) {
        alert('Aday ve pozisyon seçimi zorunludur'); return;
      }
      const candidate = candidates.value.find(c => c.id == newApp.value.candidate_id);
      if (candidate && candidate.is_blacklisted) {
        alert('DİKKAT: Kara listedeki bir aday için yeni başvuru oluşturulamaz!'); return;
      }
      try {
        await api('POST', '/api/applications/', newApp.value);
        showNewAppModal.value = false;
        newApp.value = { candidate_id: '', position_id: '', source: '', cover_letter: '' };
        loadPipeline();
      } catch (e) { alert('Başvuru eklenemedi: ' + e.message); }
    }

    async function updateAppStatus(newStatus) {
      if (!selectedApp.value || !newStatus) return;
      try {
        await api('PATCH', `/api/applications/${selectedApp.value.id}/status`, { status: newStatus });
        selectedApp.value.status = newStatus;
        loadPipeline();
      } catch (e) { alert('Durum güncellenemedi'); }
    }

    async function saveAppNotes() {
      if (!selectedApp.value) return;
      try {
        await api('PUT', `/api/applications/${selectedApp.value.id}/notes?notes=${encodeURIComponent(appNotes.value)}`);
        selectedApp.value.hr_notes = appNotes.value;
      } catch (e) { alert('Not kaydedilemedi'); }
    }

    // Drag & drop
    function dragApp(app) { draggedApp.value = app; }

    async function dropOnCol(status) {
      if (!draggedApp.value || draggedApp.value.status === status) {
        draggedApp.value = null; dragOverCol.value = null; return;
      }
      if (draggedApp.value.candidate?.is_blacklisted) {
        alert('HATA: Kara listedeki bir adayı sürece dahil edemezsiniz veya ilerletemezsiniz!');
        draggedApp.value = null; dragOverCol.value = null; return;
      }
      try {
        await api('PATCH', `/api/applications/${draggedApp.value.id}/status`, { status, note: 'Pipeline üzerinden taşındı' });
        draggedApp.value.status = status;
        loadPipeline();
      } catch (e) { alert('Durum değiştirilemedi: ' + e.message); }
      draggedApp.value = null; dragOverCol.value = null;
    }

    function createApplicationFromCandidate(c) {
      if (c.is_blacklisted) {
        alert('DİKKAT: Kara listedeki adayları sürece dahil edemezsiniz.'); return;
      }
      newApp.value.candidate_id = c.id;
      selectedCandidate.value = null;
      showNewAppModal.value = true;
    }

    // ─── INTERVIEWS ───────────────────────────────────────────────────
    async function loadAppInterviews() {
      if (!selectedApp.value) return;
      try {
        appInterviews.value = await api('GET', `/api/interviews/application/${selectedApp.value.id}`);
      } catch (e) { appInterviews.value = []; }
    }

    async function saveInterview() {
      if (!selectedApp.value) return;
      try {
        const payload = {
          ...newIv.value,
          application_id: selectedApp.value.id,
          scheduled_at: newIv.value.scheduled_at || null,
        };
        const iv = await api('POST', '/api/interviews/', payload);
        appInterviews.value.push(iv);
        showNewInterviewModal.value = false;
        newIv.value = { round_number: 1, interview_type: 'hr', scheduled_at: '', duration_minutes: 60, interviewer_name: '', meeting_link: '' };
        if (selectedApp.value) selectedApp.value.status = 'interview';
        loadPipeline();
      } catch (e) { alert('Mülakat kaydedilemedi: ' + e.message); }
    }

    async function generateQuestions(iv) {
      try {
        const res = await api('POST', `/api/interviews/${iv.id}/generate-questions`);
        iv.ai_questions = res.questions;
      } catch (e) { alert('AI soru üretilemedi: ' + e.message); }
    }

    function openFeedbackModal(iv) {
      feedbackIv.value = iv;
      ivFeedback.value = {
        overall_score: iv.overall_score || null,
        technical_score: iv.technical_score || null,
        cultural_score: iv.cultural_score || null,
        notes: iv.notes || '',
        recommendation: iv.recommendation || '',
        strengths_str: (iv.strengths_noted || []).join(', '),
        concerns_str: (iv.concerns_noted || []).join(', '),
        result: iv.result || 'pending',
        result_note: iv.result_note || '',
      };
    }

    async function saveFeedback() {
      if (!feedbackIv.value) return;
      try {
        const payload = {
          ...ivFeedback.value,
          strengths_noted: ivFeedback.value.strengths_str.split(',').map(s => s.trim()).filter(Boolean),
          concerns_noted: ivFeedback.value.concerns_str.split(',').map(s => s.trim()).filter(Boolean),
        };
        delete payload.strengths_str; delete payload.concerns_str;
        const updated = await api('POST', `/api/interviews/${feedbackIv.value.id}/feedback`, payload);
        const idx = appInterviews.value.findIndex(i => i.id === updated.id);
        if (idx >= 0) appInterviews.value[idx] = updated;
        feedbackIv.value = null;
      } catch (e) { alert('Değerlendirme kaydedilemedi: ' + e.message); }
    }

    async function generateAISummary(iv) {
      try {
        const res = await api('POST', `/api/interviews/${iv.id}/ai-summary`);
        iv.ai_summary = res.summary;
      } catch (e) { alert('AI özeti üretilemedi'); }
    }

    async function generateAiQuestionsTab() {
      if (!ivAssistant.value.candidateId || !ivAssistant.value.positionId) {
        alert('Lütfen aday ve pozisyon seçin.');
        return;
      }
      ivAssistant.value.loading = true;
      ivAssistant.value.questions = [];
      try {
        const res = await api('POST', '/api/interviews/ai/interview-questions', {
          candidate_id: parseInt(ivAssistant.value.candidateId),
          position_id: parseInt(ivAssistant.value.positionId)
        });
        ivAssistant.value.questions = res.questions || [];
      } catch (e) {
        alert('AI soruları üretilemedi: ' + e.message);
      }
      ivAssistant.value.loading = false;
    }

    async function analyzeRawNotesTab() {
      if (!ivAnalysis.value.interviewId || !ivAnalysis.value.rawNotes) {
        alert('Lütfen mülakat seçin ve ham notları girin.');
        return;
      }
      ivAnalysis.value.loading = true;
      ivAnalysis.value.result = null;
      try {
        const res = await api('POST', `/api/interviews/${ivAnalysis.value.interviewId}/analyze-notes`, {
          raw_notes: ivAnalysis.value.rawNotes
        });
        ivAnalysis.value.result = res;
        alert('Mülakat notu analizi başarıyla tamamlandı!');
        loadInitialData();
        loadAllInterviews();
      } catch (e) {
        alert('Not analizi başarısız oldu: ' + e.message);
      }
      ivAnalysis.value.loading = false;
    }

    async function openIvDetail(iv) {
      // Find the application and open it
      try {
        const app = await api('GET', `/api/applications/${iv.application_id || ''}`).catch(() => null);
        if (app) {
          selectedApp.value = app;
          appTab.value = 'interviews';
          await loadAppInterviews();
        }
      } catch (e) {}
    }

    // ─── OFFERS ───────────────────────────────────────────────────────
    async function loadOffer() {
      if (!selectedApp.value) return;
      try {
        currentOffer.value = await api('GET', `/api/offers/application/${selectedApp.value.id}`);
      } catch (e) { currentOffer.value = null; }
    }

    async function saveOffer() {
      if (!selectedApp.value) return;
      try {
        const payload = {
          application_id: selectedApp.value.id,
          proposed_salary: newOffer.value.proposed_salary,
          currency: 'TRY',
          start_date: newOffer.value.start_date || null,
          position_title: newOffer.value.position_title,
          benefits: newOffer.value.benefits_str.split(',').map(s => s.trim()).filter(Boolean),
          notes: newOffer.value.notes,
        };
        const saved = await api('POST', '/api/offers/', payload);
        currentOffer.value = saved;
        showNewOfferModal.value = false;
        newOffer.value = { proposed_salary: null, start_date: '', position_title: '', benefits_str: '', notes: '' };
        if (selectedApp.value) selectedApp.value.status = 'offer';
        loadPipeline();
      } catch (e) { alert('Teklif kaydedilemedi: ' + e.message); }
    }

    async function generateLetter() {
      if (!currentOffer.value) return;
      try {
        const res = await api('POST', `/api/offers/${currentOffer.value.id}/generate-letter`);
        currentOffer.value.letter_content = res.letter;
      } catch (e) { alert('Mektup üretilemedi: ' + e.message); }
    }

    async function sendOffer() {
      if (!currentOffer.value) return;
      try {
        await api('PATCH', `/api/offers/${currentOffer.value.id}/status?status=sent`);
        currentOffer.value.status = 'sent';
      } catch (e) { alert('Teklif gönderilemedi'); }
    }

    // ─── ONBOARDING ───────────────────────────────────────────────────
    async function loadOnboarding() {
      if (!selectedApp.value) return;
      try {
        onboardingTasks.value = await api('GET', `/api/onboarding/${selectedApp.value.id}`);
      } catch (e) { onboardingTasks.value = []; }
    }

    async function generateOnboarding() {
      if (!selectedApp.value) return;
      try {
        const res = await api('POST', `/api/onboarding/${selectedApp.value.id}/generate`);
        onboardingTasks.value = res.tasks || [];
        selectedApp.value.status = 'hired';
        loadPipeline();
      } catch (e) { alert('Onboarding oluşturulamadı: ' + e.message); }
    }

    async function updateTask(task, checked) {
      const status = checked ? 'completed' : 'pending';
      try {
        await api('PATCH', `/api/onboarding/task/${task.id}?status=${status}`);
        task.status = status;
      } catch (e) { alert('Görev güncellenemedi'); }
    }

    // ─── UPLOAD ───────────────────────────────────────────────────────
    function handleFileSelect(evt) {
      processFiles(Array.from(evt.target.files));
    }

    function handleFileDrop(evt) {
      dragover.value = false;
      processFiles(Array.from(evt.dataTransfer.files).filter(f => f.type === 'application/pdf'));
    }

    async function processFiles(files) {
      if (!files.length) return;
      for (const file of files) {
        const item = { name: file.name, size: file.size, status: 'uploading' };
        uploadQueue.value.push(item);
        try {
          const fd = new FormData();
          fd.append('file', file);
          const c = await apiForm('/api/candidates/upload', fd);
          item.status = 'done';
          candidates.value.unshift(c);
        } catch (e) {
          item.status = 'error';
        }
      }
      setTimeout(() => { if (uploadQueue.value.every(f => f.status !== 'uploading')) showUpload.value = false; }, 2000);
    }

    // ─── CHAT ─────────────────────────────────────────────────────────
    async function sendChat() {
      const msg = chatInput.value.trim();
      if (!msg) return;
      chatMessages.value.push({ id: Date.now(), role: 'user', text: msg });
      chatInput.value = '';
      chatLoading.value = true;
      await nextTick();
      if (chatMsgs.value) chatMsgs.value.scrollTop = chatMsgs.value.scrollHeight;
      try {
        const res = await api('POST', '/api/chat', { message: msg });
        chatMessages.value.push({ id: Date.now() + 1, role: 'bot', text: res.response });
      } catch (e) {
        chatMessages.value.push({ id: Date.now() + 1, role: 'bot', text: 'Üzgünüm, şu an yanıt veremiyorum.' });
      }
      chatLoading.value = false;
      await nextTick();
      if (chatMsgs.value) chatMsgs.value.scrollTop = chatMsgs.value.scrollHeight;
    }

    // ─── HELPERS ──────────────────────────────────────────────────────
    function stageColor(status) {
      const colors = {
        applied: '#3B82F6',
        screening: '#F59E0B',
        hr_interview: '#7C3AED',
        tech_interview: '#2563EB',
        manager_interview: '#8B5CF6',
        reference_check: '#EC4899',
        offer: '#D97706',
        hired: '#059669',
        rejected: '#6B7280',
        hold: '#64748B'
      };
      return colors[status] || '#6B7280';
    }

    function scoreClass(score) {
      if (score >= 70) return 'sp-high';
      if (score >= 40) return 'sp-mid';
      return 'sp-low';
    }

    function stageIndex(status) {
      const order = ['applied', 'screening', 'hr_interview', 'tech_interview', 'manager_interview', 'reference_check', 'offer', 'hired', 'rejected', 'hold'];
      return order.indexOf(status);
    }

    function ivTypeLabel(type) {
      const map = { hr: 'İK', technical: 'Teknik', video: 'Video', onsite: 'Yüz Yüze' };
      return map[type] || type;
    }

    function formatDate(dt) {
      if (!dt) return '';
      const d = new Date(dt);
      return d.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    }

    function calculateBestMatch(c) {
      if (c.best_position && c.best_position.title !== "Eşleşme Yok") {
        return { title: c.best_position.title, score: Math.round(c.best_score) };
      }
      return null;
    }



    function getHeatmapCount(skill, level) {
      if (!candidates.value) return 0;
      const lvlMap = {
        'Giriş Seviyesi': ['giriş seviyesi', 'junior', 'entry', 'giriş'],
        'Orta Seviye': ['orta seviye', 'mid', 'middle', 'orta'],
        'Kıdemli': ['kıdemli', 'senior', 'lead', 'principal', 'uzman']
      };
      const validLvls = lvlMap[level] || [level.toLowerCase()];
      return candidates.value.filter(c => {
        if (c.is_deleted) return false;
        const cSen = (c.seniority_level || '').toLowerCase();
        const hasSkill = (c.skills || []).some(s => s.toLowerCase() === skill.toLowerCase());
        const hasLevel = validLvls.some(vl => cSen.includes(vl));
        return hasSkill && hasLevel;
      }).length;
    }

    function getHeatmapColor(skill, level) {
      const count = getHeatmapCount(skill, level);
      if (count === 0) return 'rgba(11, 74, 58, 0.03)';
      if (count === 1) return 'rgba(11, 74, 58, 0.15)';
      if (count === 2) return 'rgba(11, 74, 58, 0.4)';
      if (count === 3) return 'rgba(11, 74, 58, 0.65)';
      return 'rgba(11, 74, 58, 0.9)';
    }

    function openCandidateByName(name) {
      if (!candidates.value) return;
      const cand = candidates.value.find(c => c.name === name);
      if (cand) {
        openCandidate(cand);
      }
    }

    // ─── INIT ─────────────────────────────────────────────────────────
    onMounted(async () => {
      // SPA route checking for candidate profile
      const path = window.location.pathname;
      const candMatch = path.match(/^\/candidates\/(\d+)/);
      if (candMatch) {
        page.value = 'candidate_profile';
        await loadFullCandidateProfile(parseInt(candMatch[1]));
      } else {
        await loadInitialData();
      }
    });

    watch(page, async (p) => {
      if (p === 'pipeline') loadPipeline();
      if (p === 'analytics' || p === 'tracking') loadAnalytics();
      if (p === 'interviews') loadAllInterviews();

      // Synchronize browser URL history with current page state
      const reversePathMap = {
        dashboard: '/',
        talent: '/candidates',
        pipeline: '/pipeline',
        analytics: '/analytics',
        jobs: '/positions',
        interviews: '/interviews',
        tasks: '/tasks',
        ai_search: '/ai_search',
        users: '/users'
      };
      const targetPath = reversePathMap[p] || '/';
      if (window.location.pathname !== targetPath) {
        window.history.pushState(null, '', targetPath);
      }
    });

    // Handle browser back and forward button navigation
    window.addEventListener('popstate', () => {
      const matchedPage = pathMap[window.location.pathname] || 'dashboard';
      if (page.value !== matchedPage) {
        page.value = matchedPage;
      }
    });

    // --- POSITION WORKSPACE STATE ---
    const workspaceData = ref(null);
    const workspaceLoading = ref(false);
    const matchingLoading = ref(false);
    const insightsLoading = ref(false);
    const questionsGenerating = ref(false);
    const reportsGenerating = ref(false);
    const activeInterviewApp = ref(null);
    const interviewQuestions = ref([]);
    const activeQuestionIndex = ref(0);
    const candidateAnswer = ref('');
    const questionScore = ref(null);
    const recruiterNotes = ref('');
    const decisionData = ref(null);
    const activeDecisionApp = ref(null);
    const activeReportApp = ref(null);
    const selectedReportType = ref('');

    async function loadWorkspace(positionId) {
      workspaceLoading.value = true;
      workspaceData.value = null;
      try {
        const data = await api('GET', `/api/positions/${positionId}/workspace`);
        workspaceData.value = data;
        selectedPosition.value = data.position;
        // If we have applications and no active app selected for tabs, select the first one
        if (data.applications && data.applications.length > 0) {
          if (!activeInterviewApp.value) activeInterviewApp.value = data.applications[0];
          if (!activeDecisionApp.value) activeDecisionApp.value = data.applications[0];
          if (!activeReportApp.value) activeReportApp.value = data.applications[0];
        }
      } catch (e) {
        showToast('Workspace yüklenemedi: ' + e.message, 'error');
      } finally {
        workspaceLoading.value = false;
      }
    }

    async function runWorkspaceMatching() {
      if (!selectedPosition.value) return;
      matchingLoading.value = true;
      try {
        await api('POST', `/api/positions/${selectedPosition.value.id}/matching/run`);
        showToast('AI Eşleştirme başarıyla tamamlandı.', 'success');
        await loadWorkspace(selectedPosition.value.id);
      } catch (e) {
        showToast('Eşleştirme hatası: ' + e.message, 'error');
      } finally {
        matchingLoading.value = false;
      }
    }

    async function generateWorkspaceInsights() {
      if (!selectedPosition.value) return;
      insightsLoading.value = true;
      try {
        await api('POST', `/api/positions/${selectedPosition.value.id}/ai-insights/generate`);
        showToast('AI Öngörüleri başarıyla oluşturuldu.', 'success');
        await loadWorkspace(selectedPosition.value.id);
      } catch (e) {
        showToast('AI Öngörü hatası: ' + e.message, 'error');
      } finally {
        insightsLoading.value = false;
      }
    }

    async function addCandidateToWorkspace(candidateId) {
      if (!selectedPosition.value) return;
      try {
        await api('POST', `/api/positions/${selectedPosition.value.id}/candidates`, { candidate_id: candidateId });
        showToast('Aday pozisyona başarıyla eklendi.', 'success');
        await loadWorkspace(selectedPosition.value.id);
      } catch (e) {
        showToast('Aday eklenemedi: ' + e.message, 'error');
      }
    }

    async function updateApplicationStageInWorkspace(appId, stage) {
      try {
        await api('PATCH', `/api/applications/${appId}/stage`, { stage });
        showToast('Aday aşaması güncellendi.', 'success');
        if (selectedPosition.value) {
          await loadWorkspace(selectedPosition.value.id);
        }
      } catch (e) {
        showToast('Aşama güncellenemedi: ' + e.message, 'error');
      }
    }

    async function generateInterviewQuestionsForCandidate(appId) {
      if (!selectedPosition.value) return;
      questionsGenerating.value = true;
      try {
        const qList = await api('POST', `/api/positions/${selectedPosition.value.id}/interview-questions/generate`, { 
          application_id: appId,
          interview_type: workspaceInterviewType.value
        });
        interviewQuestions.value = qList;
        activeQuestionIndex.value = 0;
        // reset fields
        candidateAnswer.value = '';
        questionScore.value = null;
        recruiterNotes.value = '';
        showToast('AI Mülakat soruları başarıyla üretildi.', 'success');
      } catch (e) {
        showToast('Soru üretilemedi: ' + e.message, 'error');
      } finally {
        questionsGenerating.value = false;
      }
    }

    async function loadInterviewAnswersForCandidate(appId, type = 'HR') {
      try {
        const answers = await api('GET', `/api/applications/${appId}/interviews?type=${type}`);
        interviewQuestions.value = answers || [];
        activeQuestionIndex.value = 0;
        // load active question fields
        if (answers && answers.length > 0) {
          loadActiveQuestionFields(0);
        }
      } catch (e) {
        interviewQuestions.value = [];
      }
    }

    function loadActiveQuestionFields(index) {
      if (!interviewQuestions.value[index]) return;
      const q = interviewQuestions.value[index];
      candidateAnswer.value = q.candidate_answer || '';
      questionScore.value = q.score;
      recruiterNotes.value = q.notes || '';
    }

    async function saveInterviewQuestionAnswer() {
      if (!activeInterviewApp.value || !interviewQuestions.value[activeQuestionIndex.value]) return;
      try {
        const q = interviewQuestions.value[activeQuestionIndex.value];
        const res = await api('POST', `/api/applications/${activeInterviewApp.value.id}/interview-answers`, {
          question_index: activeQuestionIndex.value,
          candidate_answer: candidateAnswer.value,
          score: questionScore.value ? Number(questionScore.value) : null,
          notes: recruiterNotes.value,
          section: q.section,
          question: q.question,
          interview_type: workspaceInterviewType.value
        });
        showToast('Mülakat yanıtı ve puanı kaydedildi.', 'success');
        
        // Update local item
        interviewQuestions.value[activeQuestionIndex.value] = res;
        
        // Progress to next question if available
        if (activeQuestionIndex.value < interviewQuestions.value.length - 1) {
          activeQuestionIndex.value++;
          loadActiveQuestionFields(activeQuestionIndex.value);
        } else {
          showToast('Mülakat başarıyla tamamlandı.', 'success');
          // Reload workspace so that sidebar status badges update
          if (selectedPosition.value) {
            await loadWorkspace(selectedPosition.value.id);
          }
        }
      } catch (e) {
        showToast('Puan kaydedilemedi: ' + e.message, 'error');
      }
    }

    async function loadHiringDecisionForCandidate(appId) {
      decisionData.value = {
        decision: 'hold',
        technical_score: 5,
        interview_score: 5,
        cultural_score: 5,
        hiring_confidence: 'Orta',
        strengths: [],
        concerns: [],
        recommended_salary: null,
        performance_bonus: null,
        start_date: '',
        work_model: 'Ofis'
      };
      try {
        const dec = await api('GET', `/api/applications/${appId}/decision`);
        if (dec) {
          decisionData.value = dec;
        }
      } catch (e) {
        // Not found is fine, we use default
      }
    }

    async function saveHiringDecision(decisionType) {
      if (!activeDecisionApp.value) return;
      try {
        const payload = {
          decision: decisionType,
          technical_score: decisionData.value.technical_score ? Number(decisionData.value.technical_score) : null,
          interview_score: decisionData.value.interview_score ? Number(decisionData.value.interview_score) : null,
          cultural_score: decisionData.value.cultural_score ? Number(decisionData.value.cultural_score) : null,
          hiring_confidence: decisionData.value.hiring_confidence,
          strengths: Array.isArray(decisionData.value.strengths) ? decisionData.value.strengths : [],
          concerns: Array.isArray(decisionData.value.concerns) ? decisionData.value.concerns : [],
          recommended_salary: decisionData.value.recommended_salary ? Number(decisionData.value.recommended_salary) : null,
          performance_bonus: decisionData.value.performance_bonus ? Number(decisionData.value.performance_bonus) : null,
          start_date: decisionData.value.start_date,
          work_model: decisionData.value.work_model
        };
        await api('POST', `/api/applications/${activeDecisionApp.value.id}/decision`, payload);
        showToast('İşe alım kararı başarıyla kaydedildi.', 'success');
        await loadWorkspace(selectedPosition.value.id);
      } catch (e) {
        showToast('Karar kaydedilemedi: ' + e.message, 'error');
      }
    }

    async function generateReportForPosition(reportType) {
      if (!selectedPosition.value || !activeReportApp.value) return;
      reportsGenerating.value = true;
      try {
        await api('POST', `/api/reports/position/${selectedPosition.value.id}/generate`, {
          application_id: activeReportApp.value.id,
          report_type: reportType
        });
        showToast(`${reportType} başarıyla oluşturuldu.`, 'success');
        await loadWorkspace(selectedPosition.value.id);
      } catch (e) {
        showToast('Rapor üretilemedi: ' + e.message, 'error');
      } finally {
        reportsGenerating.value = false;
      }
    }

    // Reset selectedPosition when page changes
    watch(page, (newPage) => {
      if (newPage !== 'jobs') {
        selectedPosition.value = null;
      }
    });

    // Watchers for Active tab selection changes in Workspace
    watch(activeInterviewApp, (newApp) => {
      if (newApp) {
        loadInterviewAnswersForCandidate(newApp.id);
      }
    });

    watch(activeDecisionApp, (newApp) => {
      if (newApp) {
        loadHiringDecisionForCandidate(newApp.id);
      }
    });

    const posSearchQuery = ref('');
    const selectedDepPill = ref('Tümü');

    const filteredPositions = computed(() => {
      let list = positions.value;
      const q = posSearchQuery.value.toLowerCase().trim();
      if (q) {
        list = list.filter(p => 
          (p.title || '').toLowerCase().includes(q) || 
          (p.department || '').toLowerCase().includes(q)
        );
      }
      if (selectedDepPill.value !== 'Tümü') {
        list = list.filter(p => 
          (p.department || '').toLowerCase() === selectedDepPill.value.toLowerCase()
        );
      }
      return list;
    });    const trackingData = computed(() => {
      return {
        upcomingInterviews: allInterviews.value.filter(iv => iv.status === 'scheduled'),
        recentLogs: logs.value.slice(0, 10),
        pendingApps: pipeline.value.reduce((acc, col) => acc.concat(col.applications || []), []).filter(a => a.status === 'applied' || a.status === 'screening')
      };
    });


    // --- 6 MODULES REDESIGN HELPER FUNCTIONS ---
    
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
      const completed = questions.filter(q => q.score !== null && q.score !== undefined && q.score !== '' && !isNaN(Number(q.score)));
      if (!completed.length) return 'Henüz puanlanmadı';
      const avg = completed.reduce((sum, q) => sum + Number(q.score), 0) / completed.length;
      return `${avg.toFixed(1)} / 10`;
    }

    function getInterviewStatusText(app) {
      if (!app) return 'Sürüyor';
      const type = workspaceInterviewType.value;
      const status = type === 'TECHNICAL' ? app.tech_status : app.hr_status;
      if (status === 'completed') return 'Tamamlandı';
      if (status === 'scheduled') return 'Planlandı';
      return 'Sürüyor';
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
      alert(`Etkinlik: ${evt.title}\nTipi: ${evt.event_type}\nAçıklama: ${evt.description || '—'}\nTarih: ${formatDate(evt.start_time)}`);
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
    
    
    return {
      // state
      workspaceInterviewType,
      hrInterviewAnswers,
      setWorkspaceInterviewType,
      selectInterviewApp,
      getAverageScoreText,
      getInterviewStatusText,
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
      
      page, talentView, candidates, positions, stats, pipeline, pipelineLoading,
      pipelinePositionFilter, allInterviews, pipelineStats,
      analyticsPositionFilter, analyticsDateFilter,
      candidateSearch, talentFilter, filteredCandidates,
      selectedCandidate, candidateTab, candidateNote, candidateApps,
      selectedPosition, posTab, positionApps, positionMatches, posMatchLoading, selectedMatchCandidates, posUploads,
      deepAiResults, deepAiLoading,
      selectedApp, appTab, appNotes, appInterviews, currentOffer, onboardingTasks, showAllQ,
      showUpload, showNewPositionModal, showNewAppModal, showNewInterviewModal, showNewOfferModal,
      matchModal, newPos, newApp, newIv, newOffer,
      feedbackIv, ivFeedback, uploadQueue, dragover, draggedApp, dragOverCol,
      chatOpen, chatInput, chatMessages, chatLoading, chatMsgs,
      analyticsStats, topSkills, stages, stageLabelMap, logs, recommendedPositions, trackingData,
      toasts, showMatchDetails, currentMatchScore, matchScoreLoading,
      interviewTab, ivAssistant, ivAnalysis,
      workspaceData, workspaceLoading, matchingLoading, insightsLoading, questionsGenerating, reportsGenerating, activeInterviewApp, interviewQuestions, activeQuestionIndex, candidateAnswer, questionScore, recruiterNotes, decisionData, activeDecisionApp, activeReportApp, selectedReportType,
      posSearchQuery, selectedDepPill, filteredPositions,
      
      // New v2 states
      aiSearchQuery, aiSearchResults, aiSearchLoading, aiSearchSearched, aiSearchStats,
      recruitmentTasks, selectedTask, showTaskModal, newTask,
      selectedApplicationIds, selectedCandidateIds, selectedCandidates, showBulkActionModal, bulkActionType, bulkActionValue,
      candidateTimeline, showNewUserModal, showEditUserModal, showPasswordResetModal,
      newUser, editingUser, passwordResetData,
      showCommModal, commCandidate, commChannel, commMsgType, commTone, commText, commSubject, commLoading, commPositionId, isViewer,

      // methods
      loadPipeline, loadAnalytics, openCandidate, rateCandidate, saveNote, deleteCandidate, toggleBlacklist,
      loadCandidateApps, openMatchModal, runMatch, matchModal,
      aiGeneratePosition, savePosition, deletePosition, openMatchPosition, openPositionDetail, loadPositionApps, loadPositionMatches, bulkAddCandidatesToPosition,
      openAppDetail, openNewAppForStage, saveNewApp, updateAppStatus, saveAppNotes,
      dragApp, dropOnCol, createApplicationFromCandidate,
      runDeepAIAnalysis, getCandidateForDeepAI, handlePositionCvDrop, handlePositionCvSelect, startPositionUploads,
      loadAppInterviews, saveInterview, generateQuestions,
      openFeedbackModal, saveFeedback, generateAISummary, openIvDetail,
      generateAiQuestionsTab, analyzeRawNotesTab,
      loadOffer, saveOffer, generateLetter, sendOffer,
      loadOnboarding, generateOnboarding, updateTask,
      handleFileSelect, handleFileDrop,
      sendChat,
      stageColor, scoreClass, stageIndex, ivTypeLabel, formatDate, calculateBestMatch,
      showToast, viewMatchDetails, getHeatmapCount, getHeatmapColor, openCandidateByName,
      loadWorkspace, runWorkspaceMatching, generateWorkspaceInsights, addCandidateToWorkspace, updateApplicationStageInWorkspace, generateInterviewQuestionsForCandidate, loadInterviewAnswersForCandidate, saveInterviewQuestionAnswer, loadHiringDecisionForCandidate, saveHiringDecision, generateReportForPosition,
      
      // New v2 methods
      openNewUserModal, saveNewUser, toggleUserStatus, editUser, updateUser,
      openPasswordReset, submitPasswordReset, runAiTalentSearch, viewCandidateById,
      loadRecruitmentTasks, openNewTaskModal, saveRecruitmentTask, editRecruitmentTask, deleteRecruitmentTask,
      loadCandidateTimeline, submitBulkAction,

      // Candidate communication methods
      normalizePhoneForWhatsApp, openCommunication, generateAiDraft, openInExternalChannel, copyCommText, getDaysSinceLastActivity,

      // auth
      currentUser, loginData, authMode, registerData, register, login, logout,
      allUsers, loadUsers,
    };
  }
}).mount('#app');
