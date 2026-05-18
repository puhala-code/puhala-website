#!/usr/bin/env python3
"""
publish.py — parse ledger.md → ledger.json → git push

Usage:
    python publish.py
"""
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent


def parse_ledger(path: Path) -> dict:
    text = path.read_text()

    # --- frontmatter ---
    fm = {}
    fm_match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
        text = text[fm_match.end():]

    # --- sections (each ## heading is one row) ---
    rows = []
    sections = [s.strip() for s in re.split(r'^## ', text, flags=re.MULTILINE) if s.strip()]
    for i, section in enumerate(sections, start=1):
        lines = section.splitlines()
        title = lines[0].strip()
        fields = {}
        for line in lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                fields[k.strip()] = v.strip()
        rows.append({
            'no':     str(i).zfill(2),
            'title':  title,
            'url':    fields.get('url', '#'),
            'status': fields.get('status', ''),
            'notes':  fields.get('notes', ''),
        })

    return {
        'date':       fm.get('date', datetime.now().strftime('%B %Y')),
        'this_issue': fm.get('this_issue', ''),
        'entries':    len(rows),
        'rows':       rows,
    }


def git_push(data: dict):
    out_path = ROOT / 'ledger.json'
    out_path.write_text(json.dumps(data, indent=2) + '\n')

    subprocess.run(['git', 'add', 'ledger.md', 'ledger.json'], check=True, cwd=ROOT)
    subprocess.run(['git', 'commit', '-m', f'ledger: {data["date"]}'], check=True, cwd=ROOT)
    subprocess.run(['git', 'push'], check=True, cwd=ROOT)

    print(f'Published {data["entries"]} entries for {data["date"]}')


if __name__ == '__main__':
    data = parse_ledger(ROOT / 'ledger.md')
    git_push(data)
