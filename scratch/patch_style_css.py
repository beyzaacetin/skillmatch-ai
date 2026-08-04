import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Replace the :root block (lines 3-16 in original file)
# The original starts with :root{ and ends with }
import re
root_pattern = r':root\s*\{[^}]*\}'
new_root = """:root{
  --primary:#0F6B57;--primary-light:#E6F0ED;--primary-hover:#0C5848;
  --sidebar-w:240px;--header-h:64px;
  --g50:#F6F8F7;--g100:#F3F4F6;--g200:#E5E7EB;--g300:#D1D5DB;
  --g400:#9CA3AF;--g500:#6B7280;--g600:#4B5563;--g700:#374151;--g900:#111827;
  --green:#16A34A;--green-bg:#DCFCE7;
  --blue:#2563EB;--blue-bg:#DBEAFE;
  --amber:#F59E0B;--amber-bg:#FEF3C7;
  --red:#DC2626;--red-bg:#FEE2E2;
  --purple:#8B5CF6;--purple-bg:#F3E8FF;
  --r:12px;--rl:20px;--ri:12px;--rb:12px;
  --sh:0 1px 2px rgba(0,0,0,.03);
  --sh-md:0 4px 6px -1px rgba(0,0,0,.02);
  --sh-lg:0 10px 15px -3px rgba(0,0,0,.02);
}"""

css_modified, count = re.subn(root_pattern, new_root, css, count=1)
if count > 0:
    print("Successfully replaced :root block")
else:
    print("Failed to replace :root block")

# Replace sidebar and main classes to hide sidebar and expand main content
sidebar_pattern = r'\.sidebar\s*\{[^}]*\}'
new_sidebar = """.sidebar{display:none !important}"""
css_modified, count = re.subn(sidebar_pattern, new_sidebar, css_modified, count=1)

main_pattern = r'\.main\s*\{[^}]*\}'
new_main = """.main{margin-left:0 !important;padding-top:64px;flex:1;min-height:100vh;display:flex;flex-direction:column}"""
css_modified, count = re.subn(main_pattern, new_main, css_modified, count=1)

# Append drawer panel CSS at the end
drawer_css = """
/* CANDIDATE SIDE PANEL DRAWER & CUSTOM UTILS */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.4);
  z-index: 1040;
  display: flex;
  justify-content: flex-end;
}
.drawer-panel {
  width: 480px;
  height: 100vh;
  background: #FFFFFF;
  border-left: 1px solid var(--g200);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1050;
  padding: 24px;
  overflow-y: auto;
}
.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--g100);
  padding-bottom: 16px;
}
.drawer-close {
  background: var(--g100);
  border: none;
  font-size: 20px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--g500);
  transition: background 0.15s;
}
.drawer-close:hover {
  background: var(--g200);
}
.drawer-section {
  margin-bottom: 24px;
}
.drawer-section-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--g400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}
.score-pill-large {
  font-size: 24px;
  font-weight: 800;
  color: var(--primary);
}
.comm-btn-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.comm-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  border-radius: 12px;
  border: 1px solid var(--g200);
  background: #FFF;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 11px;
  font-weight: 600;
  color: var(--g700);
  gap: 6px;
}
.comm-btn:hover {
  background: var(--g50);
  border-color: var(--g300);
}
.circle-progress-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 120px;
  height: 120px;
}
.circle-progress-text {
  position: absolute;
  text-align: center;
}
.circle-progress-pct {
  font-size: 28px;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
}
.circle-progress-lbl {
  font-size: 9px;
  color: var(--g500);
  font-weight: 600;
  text-transform: uppercase;
  margin-top: 2px;
}
"""

css_modified += drawer_css

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_modified)

print("style.css successfully patched")
