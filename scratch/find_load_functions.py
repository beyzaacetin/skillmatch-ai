import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

app_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\app.js"

with open(app_path, "r", encoding="utf-8") as f:
    js = f.read()

# Let's find function declarations in Vue setup.
# In Vue 3 setup, functions are usually written like:
# const load... = async (...) => or function load...
matches = re.finditer(r'(const\s+load\w+|function\s+load\w+|const\s+fetch\w+|function\s+fetch\w+)\s*=\s*(async\s*)?\(', js)
print("Found load/fetch functions:")
for m in matches:
    start = m.start()
    # Find the line containing this match
    line_start = js.rfind('\n', 0, start) + 1
    line_end = js.find('\n', start)
    print(js[line_start:line_end].strip())
