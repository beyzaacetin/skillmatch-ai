import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"backend/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's trace position_workspace section from line 743 to 2098
stack = []
for idx in range(742, 2095):
    line = lines[idx]
    # Find all tags in line
    tags = re.findall(r'<(div|template)\b[^>]*>|</(div|template)>', line)
    for tag in tags:
        # tag is e.g. ('div', '') or ('', 'div')
        is_opening = bool(tag[0])
        tag_name = tag[0] if is_opening else tag[1]
        
        if is_opening:
            stack.append((tag_name, idx + 1, line.strip()))
        else:
            if not stack:
                print(f"[{idx+1}] Unexpected closing tag </{tag_name}>: {line.strip()}")
            else:
                last_name, start_line, src = stack.pop()
                if last_name != tag_name:
                    print(f"[{idx+1}] Mismatched tag </{tag_name}>: expected </{last_name}> (opened at line {start_line}: {src})")
                    # Put it back to keep tracking or not
                    stack.append((last_name, start_line, src))

print("\n--- Remaining stack ---")
for t, l, src in stack:
    print(f"Line {l}: <{t}> - {src}")
