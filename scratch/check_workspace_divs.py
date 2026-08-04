import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"backend/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Scan from line 740 to 2105
# Let's count divs and template tags
open_tags = []
for idx in range(740, 2105):
    line = lines[idx]
    # Simple tag finding
    # Let's look for <div or </div> or <template or </template>
    import re
    tags = re.findall(r'<(div|template)\b|</(div|template)>', line)
    for tag in tags:
        # tag is a tuple e.g. ('div', '') or ('', 'div')
        is_opening = bool(tag[0])
        tag_name = tag[0] if is_opening else tag[1]
        
        if is_opening:
            open_tags.append((tag_name, idx + 1))
        else:
            if not open_tags:
                print(f"Unexpected closing tag </{tag_name}> at line {idx+1}")
            else:
                last_name, start_line = open_tags.pop()
                if last_name != tag_name:
                    print(f"Mismatched tag </{tag_name}> at line {idx+1} (expected </{last_name}> from line {start_line})")

print("Remaining open tags at the end of position_workspace section:")
for t, l in open_tags:
    print(f"Tag <{t}> from line {l}")
