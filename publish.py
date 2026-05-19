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


def parse_photos(path: Path) -> dict:
    text = path.read_text()

    fm = {}
    fm_match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
        text = text[fm_match.end():]

    photos = {}
    for section in re.split(r'^## ', text, flags=re.MULTILINE):
        section = section.strip()
        if not section:
            continue
        lines = section.splitlines()
        photo_id = lines[0].strip()
        fields = {}
        for line in lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                fields[k.strip()] = v.strip()
        photos[photo_id] = {
            'url':           fields.get('url', ''),
            'alt':           fields.get('alt', ''),
            'caption_left':  fields.get('caption_left', ''),
            'caption_right': fields.get('caption_right', ''),
        }

    return {
        'date':     fm.get('date', ''),
        'location': fm.get('location', ''),
        'photos':   photos,
    }


def git_push(ledger: dict, photos: dict):
    (ROOT / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    (ROOT / 'photos.json').write_text(json.dumps(photos, indent=2) + '\n')

    subprocess.run(
        ['git', 'add',
         'ledger.md', 'ledger.json',
         'photos.md', 'photos.json',
         'squarespace-bundle.html',
         'squarespace-header-inject.css',
         'publish.py'],
        check=True, cwd=ROOT,
    )
    subprocess.run(
        ['git', 'commit', '-m', f'publish: {ledger["date"]}'],
        check=True, cwd=ROOT,
    )
    subprocess.run(['git', 'push'], check=True, cwd=ROOT)

    print(f'Published ledger ({ledger["entries"]} entries) + photos ({len(photos["photos"])} slots) for {ledger["date"]}')


if __name__ == '__main__':
    ledger = parse_ledger(ROOT / 'ledger.md')
    photos = parse_photos(ROOT / 'photos.md')
    git_push(ledger, photos)
