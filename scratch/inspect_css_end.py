import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

lines = css.split("\n")
print(f"Total lines in style.css: {len(lines)}")
# Print last 50 lines
for idx, line in enumerate(lines[-50:]):
    print(f"{len(lines)-50+idx+1}: {line}")
