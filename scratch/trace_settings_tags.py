import re
from html.parser import HTMLParser

class SettingsTagTracer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag not in self_closing:
            self.tags.append((tag, self.getpos()))
            line, col = self.getpos()
            if line >= 3108 and line <= 3735:
                print(f"[{line}] OPEN <{tag}> (Stack depth: {len(self.tags)})")

    def handle_endtag(self, tag):
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag in self_closing:
            return
        if self.tags:
            last_tag, pos = self.tags.pop()
            line, col = self.getpos()
            if line >= 3108 and line <= 3735:
                print(f"[{line}] CLOSE </{tag}> (Closed <{last_tag}> from line {pos[0]})")
        else:
            line, col = self.getpos()
            if line >= 3108 and line <= 3735:
                print(f"[{line}] UNEXPECTED CLOSE </{tag}>")

index_path = r"backend/templates/index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html_content = f.read()

html_clean = re.sub(r'\{\{.*?\}\}', '', html_content)
html_clean = re.sub(r'\{%.*?%\}', '', html_clean)

parser = SettingsTagTracer()
parser.feed(html_clean)
