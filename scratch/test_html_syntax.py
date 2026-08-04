import sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

class TagValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        # Ignore self-closing tags in HTML5
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag not in self_closing:
            self.tags.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        self_closing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr']
        if tag in self_closing:
            return
        if not self.tags:
            self.errors.append(f"Unexpected end tag </{tag}> at line {self.getpos()[0]}, col {self.getpos()[1]}")
            return
        last_tag, pos = self.tags.pop()
        if last_tag != tag:
            self.errors.append(f"Mismatched tag </{tag}> at line {self.getpos()[0]} (expected </{last_tag}> from line {pos[0]}, col {pos[1]})")

index_path = r"backend/templates/index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Remove Vue template expressions or raw/endraw blocks that might confuse parser
import re
html_clean = re.sub(r'\{\{.*?\}\}', '', html_content)
html_clean = re.sub(r'\{%.*?%\}', '', html_clean)

parser = TagValidator()
parser.feed(html_clean)

if parser.errors:
    print(f"Found {len(parser.errors)} syntax errors:")
    for err in parser.errors[:20]:
        print(err)
else:
    print("HTML syntax is valid! All opened tags are closed correctly.")
