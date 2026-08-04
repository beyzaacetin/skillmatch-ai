index_path = r"c:\Users\sule\OneDrive - Fine Otel Turizm İşletmecilik A.S\Desktop\skillmatch_v4\backend\templates\index.html"

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

start_tag = '<template v-if="page===\'tasks\'">'
end_tag = '</template>'

start_idx = html.find(start_tag)
if start_idx != -1:
    print(f"Start index found at: {start_idx}")
    # find next </template>
    end_idx = html.find(end_tag, start_idx + len(start_tag))
    print(f"End index found at: {end_idx}")
    print(html[start_idx:start_idx+100])
else:
    print("Start tag not found!")
