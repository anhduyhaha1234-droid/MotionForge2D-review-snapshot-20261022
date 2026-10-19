from pathlib import Path
import argparse, ast, collections, datetime, hashlib, json
ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=Path(a.manifest);m=json.loads(mp.read_text(encoding='utf-8-sig'));pre=json.loads((OUT/'C02A_PREFLIGHT.json').read_text())
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':sha(mp),'candidate':[],'protected':[],'duplicates':[]}
for f in m['files']:
    rec['candidate'].append({'path':f['source'],'source_match':sha(f['source'])==f['sha256'],'snapshot_match':sha(f['snapshot'])==f['sha256']})
    tree=ast.parse(Path(f['source']).read_text(encoding='utf-8'))
    for parent in ast.walk(tree):
        if isinstance(parent,(ast.Module,ast.ClassDef)):
            counts=collections.Counter(n.name for n in parent.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
            rec['duplicates'].extend({'file':f['relative'],'name':n,'count':v} for n,v in counts.items() if v>1)
for f in pre['files']:
    if f['role']=='protected':rec['protected'].append({'path':f['path'],'unchanged':sha(f['path'])==f['sha256']})
root=Path(pre['files'][0]['path']).parents[1]
known={Path(f['path']).resolve() for f in pre['files']}|{Path(pre['new_test']).resolve()}
rec['unexpected_new_files']=[str(p) for directory in ('scripts','tests') for p in (root/directory).glob('*.py') if p.resolve() not in known]
original=json.loads((OUT/'PREFLIGHT.json').read_text())
rec['media']=[{'label':label,'unchanged':sha(f['path'])==f['sha256']} for label,f in original['media'].items()]
rec['pinned_artifacts']=[{'path':f['path'],'match':sha(f['path'])==f['sha256']} for group in ('diffs','receipts') for f in m.get(group,[])]
def assertions(p):
    t=ast.parse(Path(p).read_text(encoding='utf-8'));return {f.name:[ast.dump(n,include_attributes=False) for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and (n.func.attr.startswith('assert') or n.func.attr=='fail')] for f in ast.walk(t) if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')}
b=next(f for f in pre['files'] if f['relative']=='tests/test_codex_c01_review_binding.py');old,new=assertions(b['snapshot']),assertions(b['path'])
rec['c01_assertions']={'baseline_test_count':len(old),'current_test_count':len(new),'identical':old==new,'differing_methods':[name for name in set(old)|set(new) if old.get(name)!=new.get(name)]}
rec['ok']=all(x['source_match'] and x['snapshot_match'] for x in rec['candidate']) and all(x['unchanged'] for x in rec['protected']) and all(x['match'] for x in rec['pinned_artifacts']) and old==new and not rec['duplicates'] and not rec['unexpected_new_files'] and all(x['unchanged'] for x in rec['media'])
p=Path(a.out);assert not p.exists();p.write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'protected':len(rec['protected']),'candidate':len(rec['candidate']),'c01_assertions':rec['c01_assertions'],'duplicates':rec['duplicates'],'receipt':str(p)}))
raise SystemExit(0 if rec['ok'] else 1)
