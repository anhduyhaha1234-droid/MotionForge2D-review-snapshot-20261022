"""Validate BOM skill structure. Place in scripts/ alongside skills/ directory."""
from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
errors=[]
for f in sorted((root/'skills').glob('*/SKILL.md')):
    text=f.read_text(encoding='utf-8')
    m=re.match(r'^---\n(.*?)\n---\n',text,re.S)
    if not m:
        errors.append(f"{f}: missing YAML frontmatter")
        continue
    fm=m.group(1)
    name=re.search(r'^name:\s*(.+)$',fm,re.M)
    desc=re.search(r'^description:\s*(.+)$',fm,re.M)
    if not name or name.group(1).strip()!=f.parent.name:
        errors.append(f"{f}: name must match directory")
    if not desc or len(desc.group(1).strip())>60:
        errors.append(f"{f}: description missing or >60 chars")
    for section in ['## When to Use','## Required Inputs','## Procedure','## Decision Rules','## Pitfalls','## Verification','## Output Format']:
        if section not in text:
            errors.append(f"{f}: missing {section}")
    if len(text.split())>5000:
        errors.append(f"{f}: exceeds 5000 words")
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(f"PASS: validated {len(list((root/'skills').glob('*/SKILL.md')))} skills")
