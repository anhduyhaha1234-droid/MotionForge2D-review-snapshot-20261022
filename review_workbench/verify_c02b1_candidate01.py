from pathlib import Path
import ast,collections,datetime,hashlib,json,os,subprocess,sys
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015');R6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mfile=OUT/'c02b1-worker/candidate-01/MANIFEST.json';m=json.loads(mfile.read_text())
pre=json.loads((OUT/'C02B1_PREFLIGHT.json').read_text())
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':sha(mfile),'candidate':[],'protected':[],'duplicates':[]}
for name,f in m['files'].items():
    rec['candidate'].append({'name':name,'live_match':sha(f['live']['path'])==f['live']['sha256'],'snapshot_match':sha(f['snapshot']['path'])==f['live']['sha256']})
    tree=ast.parse(Path(f['live']['path']).read_text(encoding='utf-8'))
    for parent in ast.walk(tree):
        if isinstance(parent,(ast.Module,ast.ClassDef)):
            counts=collections.Counter(n.name for n in parent.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
            rec['duplicates'].extend({'file':name,'name':n,'count':v} for n,v in counts.items() if v>1)
for f in pre['files']:
    if f['role']=='protected':rec['protected'].append({'path':f['path'],'unchanged':sha(f['path'])==f['sha256']})
rec['evidence']=[{'path':f['path'],'match':sha(f['path'])==f['sha256']} for f in m['evidence']]
known={Path(f['path']).resolve() for f in pre['files']}|{Path(pre['new_test']).resolve()}
rec['unexpected_new_files']=[str(p) for d in ('scripts','tests') for p in (R6/d).glob('*.py') if p.resolve() not in known]
f=next(f for f in pre['files'] if f['relative']=='scripts/r6_common.py')
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(p).read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old,new=functions(f['snapshot']),functions(f['path'])
rec['unrelated_function_changes']=[n for n,v in old.items() if n!='stage_frame' and new.get(n)!=v]
original=json.loads((OUT/'PREFLIGHT.json').read_text())
rec['media']=[{'label':label,'unchanged':sha(f['path'])==f['sha256']} for label,f in original['media'].items()]
rec['ok']=all(f['live_match'] and f['snapshot_match'] for f in rec['candidate']) and all(f['unchanged'] for f in rec['protected']+rec['media']) and all(f['match'] for f in rec['evidence']) and not any(rec[k] for k in ('duplicates','unexpected_new_files','unrelated_function_changes'))
target=OUT/'root-review/C02B1_SCOPE_CANDIDATE01.json';assert not target.exists();target.write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps({'scope_ok':rec['ok'],'protected':len(rec['protected']),'candidate':rec['candidate'],'unrelated':rec['unrelated_function_changes']}))
assert rec['ok']
root=OUT/'root-review/c02b1-tests-candidate01';root.mkdir(exist_ok=False)
env=os.environ.copy();env.update(C02B1_WORKER_DIR=str(root),C01_WORKER_DIR=str(root),C02A_WORKER_DIR=str(root))
runs=[]
for name,args in [('STAGING',['-m','unittest','-v','test_codex_c02b1_staged_source']),('REGRESSION',['-m','unittest','-v','test_codex_c01_review_binding','test_codex_c02a_dependency_verification'])]:
    cmd=[sys.executable,'-B','-X','utf8',*args];r=subprocess.run(cmd,cwd=R6/'tests',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    p=root/(name+'.txt');p.write_bytes(r.stdout)
    row={'command':cmd,'cwd':str(R6/'tests'),'exit':r.returncode,'raw':str(p),'summary':[l for l in r.stdout.decode('utf-8','replace').splitlines() if l.startswith(('Ran ','OK','FAILED'))]};runs.append(row);print(json.dumps(row))
    if r.returncode:break
(root/'RESULT.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':runs},indent=2),encoding='utf-8')
assert len(runs)==2 and all(r['exit']==0 for r in runs)

