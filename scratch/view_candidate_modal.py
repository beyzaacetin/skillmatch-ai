import sys
sys.stdout.reconfigure(encoding='utf-8')
index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

start_index = 181086
end_index = start_index + 18000  # Let's read a good chunk
modal_html = html[start_index:end_index]
lines = modal_html.split("\n")
print(f"Candidate modal starts. Read {len(lines)} lines.")

# Look for sub-tabs and main layout
for idx, line in enumerate(lines[:120]):
    sys.stdout.write(f"Line {idx+1}: {line.strip()[:140].encode('ascii', errors='replace').decode('ascii')}\n")
