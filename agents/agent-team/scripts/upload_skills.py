#!/usr/bin/env python3
"""Create or version focused skills in an Anthropic workspace. Dry-run unless --execute is supplied."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKILLS=ROOT/'skills'
OUT=ROOT/'dist'/'skill_ids.json'

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--execute',action='store_true',help='Perform API writes. Without this flag, only validates the plan.')
    ap.add_argument('--update-existing',action='store_true',help='Create a new version when display_title already exists.')
    args=ap.parse_args()
    folders=sorted(p for p in SKILLS.iterdir() if p.is_dir())
    print(f'Plan: {len(folders)} focused skills')
    for p in folders: print(' -',p.name)
    if not args.execute:
        print('Dry run only. Re-run with --execute after reviewing the plan.')
        return
    if not os.getenv('ANTHROPIC_API_KEY'):
        raise SystemExit('ANTHROPIC_API_KEY is not set')
    try:
        import anthropic
        from anthropic.lib import files_from_dir
    except ImportError:
        raise SystemExit('Install dependencies: pip install -r requirements.txt')
    client=anthropic.Anthropic()
    existing={s.display_title:s for s in client.beta.skills.list(source='custom')}
    result={}
    failures=[]
    for folder in folders:
        try:
            prior=existing.get(folder.name)
            if prior and args.update_existing:
                v=client.beta.skills.versions.create(prior.id,files=files_from_dir(str(folder)))
                result[folder.name]={'skill_id':prior.id,'version':v.version,'action':'versioned'}
            elif prior:
                result[folder.name]={'skill_id':prior.id,'version':getattr(prior,'latest_version',None),'action':'reused'}
            else:
                s=client.beta.skills.create(display_title=folder.name,files=files_from_dir(str(folder)))
                result[folder.name]={'skill_id':s.id,'version':s.latest_version,'action':'created'}
            print('OK',folder.name,result[folder.name])
        except Exception as exc:
            failures.append({'skill':folder.name,'error':repr(exc)})
            print('FAIL',folder.name,exc,file=sys.stderr)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'skills':result,'failures':failures},indent=2),encoding='utf-8')
    print('Wrote',OUT)
    if failures: raise SystemExit(1)
if __name__=='__main__': main()
