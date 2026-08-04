index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

target = '<template v-if="currentUser">'

replacement = """<template v-if="currentUser">
  <!-- FIXED TOP NAVIGATION HEADER -->
  <header class="top-nav" style="position:fixed; top:0; left:0; right:0; height:64px; background:#FFFFFF; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; padding:0 24px; z-index:1000; box-shadow:var(--sh);">
     <div style="display:flex; align-items:center; gap:24px;">
       <a href="#" class="logo-wrap" style="text-decoration:none; display:flex; align-items:center; gap:10px;" @click.prevent="page='dashboard'">
         <svg viewBox="0 0 100 100" width="38" height="38" style="display:block; flex-shrink:0">
           <rect width="100" height="100" rx="24" fill="#0F6B57"/>
           <text x="50" y="73" font-family="'Times New Roman', 'Georgia', 'Garamond', serif" font-size="68" fill="#fff" text-anchor="middle" font-weight="700">S</text>
         </svg>
         <div class="logo-text-container" style="display:flex; flex-direction:column;">
           <div class="logo-main-text" style="font-family:'Times New Roman', Georgia, serif; font-size:16px; font-weight:700; color:#0F6B57; line-height:1.15;">SkillMatch AI</div>
           <div class="logo-sub-text" style="font-size:9px; font-weight:600; letter-spacing:0.12em; color:var(--text-secondary); margin-top:1px;">BY SRYVERSE</div>
         </div>
       </a>
       
       <nav style="display:flex; gap:16px;">
         <button class="btn btn-ghost btn-sm" :class="{active: page==='dashboard'}" @click="page='dashboard'" style="border:none; font-size:13px; font-weight:600;">Dashboard</button>
         <button class="btn btn-ghost btn-sm" :class="{active: page==='talent'}" @click="page='talent'" style="border:none; font-size:13px; font-weight:600;">Candidates</button>
         <button class="btn btn-ghost btn-sm" :class="{active: page==='jobs'}" @click="page='jobs'" style="border:none; font-size:13px; font-weight:600;">Positions</button>
         <button class="btn btn-ghost btn-sm" :class="{active: page==='tasks'}" @click="page='tasks'; loadRecruitmentTasks()" style="border:none; font-size:13px; font-weight:600;">Calendar & Tasks</button>
       </nav>
     </div>
     
     <div style="display:flex; align-items:center; gap:16px;">
       <!-- Global Search -->
       <div class="search-bar" style="min-width:280px; height:36px; display:flex; align-items:center; gap:8px; background:var(--g100); border-radius:12px; padding:0 12px;">
         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
         <input v-model="candidateSearch" type="text" placeholder="Search candidates, positions..." style="border:none; background:transparent; outline:none; font-size:12.5px; width:100%;">
       </div>
       
       <!-- Notifications -->
       <button class="btn btn-ghost" style="padding:8px; position:relative; background:transparent; border:none; cursor:pointer;" @click="alert('No new notifications')">
         <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--text-secondary);"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>
         <span style="position:absolute; top:4px; right:4px; width:8px; height:8px; background:var(--danger); border-radius:50%;"></span>
       </button>
       
       <!-- + New Button & Dropdown -->
       <div style="position:relative;">
         <button class="btn btn-primary" @click="showNewDropdown = !showNewDropdown" style="height:36px; padding:0 14px; display:flex; align-items:center; gap:4px; font-size:13px; border-radius:12px;">
           <span>+ New</span>
         </button>
         <div v-if="showNewDropdown" style="position:absolute; top:40px; right:0; background:#FFF; border:1px solid var(--border); border-radius:12px; box-shadow:var(--sh-lg); width:160px; z-index:1100; display:flex; flex-direction:column; padding:4px;">
           <button @click="showNewPositionModal=true; showNewDropdown=false" style="background:none; border:none; padding:8px 12px; text-align:left; font-size:13px; font-weight:500; color:var(--text-primary); cursor:pointer; width:100%; border-radius:8px;" class="dropdown-item">New Position</button>
           <button @click="newCandidate = {position_id: ''}; showNewCandidateModal=true; showNewDropdown=false" style="background:none; border:none; padding:8px 12px; text-align:left; font-size:13px; font-weight:500; color:var(--text-primary); cursor:pointer; width:100%; border-radius:8px;" class="dropdown-item">New Candidate</button>
         </div>
       </div>
       
       <!-- User Avatar -->
       <div class="user-av" style="cursor:pointer; width:36px; height:36px; border-radius:50%; background:var(--primary); color:#FFF; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px;" @click="logout" title="Click to logout">
         {{ (currentUser.full_name || 'JO').split(' ').map(n=>n[0]).join('') }}
       </div>
     </div>
  </header>"""

if target in html:
    # Only replace first occurrence
    html = html.replace(target, replacement, 1)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Fixed top nav header patched successfully!")
else:
    print("template tag not found in index.html")
