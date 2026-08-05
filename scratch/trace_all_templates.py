import re
from html.parser import HTMLParser

class TemplateTracer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.current_template = None

    def handle_starttag(self, tag, attrs):
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag not in self_closing:
            self.tags.append((tag, self.getpos()))
            line, col = self.getpos()
            
            # Check if template tag
            if tag == 'template':
                # Print attrs to see which template it is
                attr_str = " ".join([f'{k}="{v}"' for k, v in attrs])
                self.current_template = (line, attr_str)
                print(f"\n--- [{line}] START TEMPLATE: {attr_str} ---")

    def handle_endtag(self, tag):
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag in self_closing:
            return
        
        if self.tags:
            last_tag, pos = self.tags.pop()
            line, col = self.getpos()
            if tag == 'template':
                print(f"--- [{line}] END TEMPLATE (Opened from line {pos[0]}) ---")
                # Print stack if not empty
                open_inside = [t for t in self.tags if t[1][0] > pos[0]]
                if open_inside:
                    print(f"    WARNING: Unclosed tags inside this template: {open_inside}")
            elif self.current_template:
                # If we're inside a template, print mismatch if last tag doesn't match
                if last_tag != tag:
                    print(f"    [{line}] MISMATCH: </{tag}> closes <{last_tag}> (from line {pos[0]})")
        else:
            line, col = self.getpos()
            print(f"    [{line}] UNEXPECTED CLOSE </{tag}>")

index_path = r"backend/templates/index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html_content = f.read()

html_clean = re.sub(r'\{\{.*?\}\}', '', html_content)
html_clean = re.sub(r'\{%.*?%\}', '', html_clean)

parser = TemplateTracer()
parser.feed(html_clean)
