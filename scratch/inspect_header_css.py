import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Find occurrences of header or top-nav in CSS
lines = css.split("\n")
for idx, line in enumerate(lines):
    if "header" in line or "page-hdr" in line or "top" in line:
        print(f"Line {idx+1}: {line.strip()}")
