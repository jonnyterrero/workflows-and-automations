#!/usr/bin/env python3
"""Validate and package focused Agent Skills. Does not build a combined router skill."""
from __future__ import annotations
from pathlib import Path
import hashlib, re, shutil, zipfile

ROOT=Path(__file__).resolve().parents[1]
SKILLS=ROOT/'skills'
DIST=ROOT/'dist'/'skills'
NAME_RE=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SECRET_PATTERNS=[re.compile(p,re.I) for p in [r'sk-ant-[A-Za-z0-9_-]{10,}',r'AKIA[0-9A-Z]{16}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]

def parse_frontmatter(text:str)->dict[str,str]:
    if not text.startswith('---\n'):
        raise ValueError('SKILL.md must start with YAML frontmatter')
    _,fm,_=text.split('---',2)
    # Parse as real YAML when available. A regex read happily accepts frontmatter
    # that a YAML loader rejects (e.g. an unquoted scalar containing ": "), which
    # ships a skill whose description silently falls back to the H1 heading.
    try:
        import yaml
    except ImportError:
        yaml=None
    if yaml is not None:
        try:
            data=yaml.safe_load(fm)
        except yaml.YAMLError as exc:
            raise ValueError(f'frontmatter is not valid YAML: {exc}') from exc
        if not isinstance(data,dict):
            raise ValueError('frontmatter must be a YAML mapping')
        for key in ('name','description'):
            if not data.get(key): raise ValueError(f'missing {key}')
            if not isinstance(data[key],str): raise ValueError(f'{key} must be a string')
        return {k:str(data[k]).strip() for k in ('name','description')}
    out={}
    for key in ('name','description'):
        m=re.search(rf'^{key}:\s*(.+)$',fm,re.M)
        if not m: raise ValueError(f'missing {key}')
        out[key]=m.group(1).strip().strip('"\'')
    return out

SMART_QUOTES={'“':'"','”':'"','‘':"'",'’':"'"}

def markdown_prose(text:str)->str:
    """Return Markdown outside fenced code blocks for prose-only checks."""
    prose=[]
    fence=None
    for line in text.splitlines():
        stripped=line.lstrip()
        marker=next((m for m in ('```','~~~') if stripped.startswith(m)),None)
        if marker:
            if fence is None:
                fence=marker
            elif marker==fence:
                fence=None
            continue
        if fence is None:
            prose.append(line)
    return '\n'.join(prose)

def check_frontmatter_chars(text:str)->None:
    """Smart quotes in frontmatter parse as literal scalar text, not string delimiters."""
    fm=text.split('---',2)[1]
    found=sorted({c for c in fm if c in SMART_QUOTES})
    if found:
        pairs=', '.join(f'{c!r} (U+{ord(c):04X}) -> {SMART_QUOTES[c]!r}' for c in found)
        raise ValueError(f'smart quote(s) in frontmatter; replace with ASCII: {pairs}')

def validate(folder:Path)->None:
    p=folder/'SKILL.md'
    if not p.exists(): raise ValueError('missing SKILL.md')
    text=p.read_text(encoding='utf-8')
    check_frontmatter_chars(text)
    meta=parse_frontmatter(text)
    name=meta['name']; desc=meta['description']
    if name!=folder.name: raise ValueError(f'name {name!r} must match folder {folder.name!r}')
    if not NAME_RE.fullmatch(name) or len(name)>64: raise ValueError('invalid name')
    if 'anthropic' in name or 'claude' in name: raise ValueError('reserved word in name')
    if not (1<=len(desc)<=200): raise ValueError(f'description length {len(desc)} outside Claude.ai 1..200')
    if len(text.splitlines())>500: raise ValueError('SKILL.md exceeds 500 recommended lines')
    if re.search(r'^ {4,}#{1,6}\s', markdown_prose(text), re.M):
        raise ValueError('indented Markdown heading detected; headings would render as code')
    for f in folder.rglob('*'):
        if f.is_symlink(): raise ValueError(f'symlink not allowed: {f}')
        if f.is_file():
            data=f.read_bytes()
            if b'../' in data and f.suffix in {'.md','.py','.sh','.js'}:
                print(f'WARN {name}: review parent-path reference in {f.name}')
            sample=data.decode('utf-8','ignore')
            for pat in SECRET_PATTERNS:
                if pat.search(sample): raise ValueError(f'possible hardcoded secret in {f}')

def main()->None:
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    sums=[]
    for folder in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        validate(folder)
        zp=DIST/f'{folder.name}.zip'
        with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(folder.rglob('*')):
                if f.is_file(): z.write(f,arcname=f'{folder.name}/{f.relative_to(folder).as_posix()}')
        digest=hashlib.sha256(zp.read_bytes()).hexdigest()
        sums.append(f'{digest}  {zp.name}')
        print('OK',zp.name)
    (DIST/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    print(f'Built {len(sums)} focused skills. Upload individually; do not combine role skills into one router.')
if __name__=='__main__': main()
