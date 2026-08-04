import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\static\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Let's show first 120 lines
lines = css.split("\n")
for idx, line in enumerate(lines[:120]):
    print(f"{idx+1}: {line}")
