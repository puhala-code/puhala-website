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


def md_to_html(text: str) -> str:
    """Convert plain paragraphs with **bold** and *italic* to HTML."""
    paras = [p.strip() for p in text.strip().split('\n\n') if p.strip()]
    result = []
    for p in paras:
        p = p.replace('\n', ' ')
        p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)
        p = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         p)
        result.append(f'<p>{p}</p>')
    return ''.join(result)


def inline_md(text: str) -> str:
    """Convert **bold** and *italic* inline — no <p> wrapper."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         text)
    return text


def parse_btp(path: Path) -> dict:
    text = path.read_text()

    fm = {}
    fm_match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
        text = text[fm_match.end():]

    weeks = []
    faq = []
    testimonials = []

    for section in re.split(r'^## ', text, flags=re.MULTILINE):
        section = section.strip()
        if not section:
            continue
        lines = section.splitlines()
        name = lines[0].strip().lower()
        body = '\n'.join(lines[1:])

        if name == 'weeks':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                week_id = ilines[0].strip()
                rest = '\n'.join(ilines[1:])
                # Split key:value header from prose body (separated by blank line)
                parts = re.split(r'\n\n', rest, maxsplit=1)
                fields = {}
                for line in parts[0].splitlines():
                    if ':' in line:
                        k, v = line.split(':', 1)
                        fields[k.strip()] = v.strip()
                prose = parts[1].strip() if len(parts) > 1 else ''
                delivery = fields.get('delivery', '').replace(' | ', '<br>')
                weeks.append({
                    'id':              week_id,
                    'kicker':          fields.get('kicker', ''),
                    'delivery':        delivery,
                    'title':           fields.get('title', ''),
                    'body':            md_to_html(prose),
                    'deliverable_lbl': fields.get('deliverable_lbl', ''),
                    'deliverable_val': fields.get('deliverable_val', ''),
                })

        elif name == 'faq':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                q = ilines[0].strip()
                a = '\n'.join(ilines[1:]).strip()
                if q:
                    faq.append({'q': q, 'a': a})

        elif name == 'testimonials':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                meta = ilines[0].strip()
                quote = '\n'.join(ilines[1:]).strip()
                if meta:
                    testimonials.append({'meta': meta, 'quote': quote})

    result = dict(fm)
    result['testimonials_visible'] = fm.get('testimonials_visible', 'false').lower() == 'true'
    result['weeks'] = weeks
    result['faq'] = faq
    result['testimonials'] = testimonials
    return result


def parse_dropin(path: Path) -> dict:
    text = path.read_text()

    fm = {}
    fm_match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
        text = text[fm_match.end():]

    # Apply md conversions to prose fields
    for key in ('masthead_title', 'subscribe_title'):
        if key in fm:
            fm[key] = inline_md(fm[key])
    for key in ('hero_body', 'what_body', 'subscribe_body'):
        if key in fm:
            fm[key] = md_to_html(fm[key])

    editions = []
    trio = []
    socials = []

    for section in re.split(r'^## ', text, flags=re.MULTILINE):
        section = section.strip()
        if not section:
            continue
        lines = section.splitlines()
        name = lines[0].strip().lower()
        body = '\n'.join(lines[1:])

        if name == 'editions':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                edition_no = ilines[0].strip()
                fields = {}
                for line in ilines[1:]:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        fields[k.strip()] = v.strip()
                editions.append({
                    'no':    edition_no,
                    'url':   fields.get('url', '#'),
                    'title': fields.get('title', ''),
                    'date':  fields.get('date', ''),
                })

        elif name == 'trio':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                label = ilines[0].strip()
                text_body = '\n'.join(ilines[1:]).strip()
                trio.append({'label': label, 'body': text_body})

        elif name == 'socials':
            for item in re.split(r'^### ', body, flags=re.MULTILINE):
                item = item.strip()
                if not item:
                    continue
                ilines = item.splitlines()
                platform = ilines[0].strip()
                fields = {}
                for line in ilines[1:]:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        fields[k.strip()] = v.strip()
                socials.append({
                    'platform': platform,
                    'url':      fields.get('url', '#'),
                    'handle':   fields.get('handle', ''),
                })

    result = dict(fm)
    result['editions'] = editions
    result['trio'] = trio
    result['socials'] = socials
    return result


def git_push(ledger: dict, photos: dict, btp: dict, dropin: dict):
    (ROOT / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    (ROOT / 'photos.json').write_text(json.dumps(photos, indent=2) + '\n')
    (ROOT / 'btp.json').write_text(json.dumps(btp, indent=2) + '\n')
    (ROOT / 'dropin.json').write_text(json.dumps(dropin, indent=2) + '\n')

    subprocess.run(
        ['git', 'add',
         'ledger.md',  'ledger.json',
         'photos.md',  'photos.json',
         'btp.md',     'btp.json',
         'dropin.md',  'dropin.json',
         'squarespace-bundle.html',
         'squarespace-musings.html',
         'squarespace-btp.html',
         'squarespace-dropin.html',
         'squarespace-header-inject.css',
         'squarespace-btp-header-inject.css',
         'squarespace-dropin-header-inject.css',
         'publish.py'],
        check=True, cwd=ROOT,
    )
    result = subprocess.run(
        ['git', 'commit', '-m', f'publish: {ledger["date"]}'],
        cwd=ROOT,
    )
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(result.returncode, result.args)
    subprocess.run(['git', 'push'], check=True, cwd=ROOT)

    print(f'Published ledger ({ledger["entries"]} entries) + photos ({len(photos["photos"])} slots) + btp ({len(btp["faq"])} FAQs) + dropin ({len(dropin["socials"])} socials) for {ledger["date"]}')


if __name__ == '__main__':
    ledger = parse_ledger(ROOT / 'ledger.md')
    photos = parse_photos(ROOT / 'photos.md')
    btp    = parse_btp(ROOT / 'btp.md')
    dropin = parse_dropin(ROOT / 'dropin.md')
    git_push(ledger, photos, btp, dropin)
