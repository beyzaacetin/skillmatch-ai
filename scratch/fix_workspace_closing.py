import sys

sys.stdout.reconfigure(encoding='utf-8')

index_path = r"backend/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find </template> at the end of position_workspace
# We know it starts at line 743. Let's find the </template> that comes after it before page==='interviews'
target_idx = -1
for idx in range(743, len(lines)):
    if "page==='interviews'" in lines[idx] or 'page === \'interviews\'' in lines[idx]:
        # Look back for </template>
        for i in range(idx - 1, 743, -1):
            if "</template>" in lines[i]:
                target_idx = i
                break
        break

if target_idx != -1:
    print(f"Found template end tag at line {target_idx+1}")
    # Print 8 lines before it
    for i in range(target_idx - 8, target_idx + 2):
        sys.stdout.write(f"{i+1}: {lines[i]}")
    
    # We want to replace lines from target_idx - 5 to target_idx inclusive
    # In original, lines are:
    # 2093:           </div>
    # 2094: 
    # 2095:         </div>
    # 2096:       </div>
    # 2097: 
    # 2098:     </template>
    # We want to change it to:
    #                 </div> <!-- closes workspace-body -->
    #             </template>
    
    # Let's verify line contents
    block = lines[target_idx-5 : target_idx+1]
    print("Replacing block:")
    for l in block:
        print(repr(l))
    
    new_block = [
        "        </div> <!-- closes workspace-body -->\n",
        "    </template>\n"
    ]
    lines[target_idx-5 : target_idx+1] = new_block
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Successfully removed extra closing divs")
else:
    print("Template end tag not found")
