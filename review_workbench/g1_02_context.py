from pathlib import Path
import json,hashlib,datetime,subprocess,urllib.request,sqlite3
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-02-20261018'
ident=json.loads((OUT/'CANDIDATE_IDENTITY.json').read_text(encoding='utf-8'))
candidate={x['relative']:x for x in ident['files']}
baseline=json.loads((BASE/'outputs/motionforge-codex-takeover-20261015/C02B2_PREFLIGHT.json').read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[]
for f in baseline['files']:
    if f.get('role') != 'protected': continue
    p=Path(f['path']); source='current live dependency'
    if f.get('relative') in candidate:
        p=Path(candidate[f['relative']]['snapshot']);source='exact submitted candidate snapshot'
    now=sha(p) if p.is_file() else None
    protected.append(dict(relative=f.get('relative'),baseline_sha=f['sha256'],review_sha=now,match=now==f['sha256'],source=source))
MG=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager')
q11=json.loads((MG/'evidence/r6/q11/Q11_R6_RACE_RESULTS.json').read_text(encoding='utf-8'))
bindings=[]
for name,field in [('dispatch_long.py','dispatch_sha256'),('invocation_runtime.py','invocation_runtime_sha256'),('terminal_contract.py','terminal_contract_sha256')]:
    p=MG/'tools'/name; now=sha(p)
    bindings.append(dict(path=str(p),current_sha=now,historical_sha=q11['provenance'][field],match=now==q11['provenance'][field]))
for rel in ('registry/SESSION_REGISTRY.json','locks/controller.lock.meta.json','evidence/r6/q11/Q11_R6_RACE_RESULTS.json','evidence/r6/q11/q11_race_suite.py','tools/invocation_runtime.py'):
    src=MG/rel; dst=OUT/'observed_manager'/rel; dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
queue={}
try:
    with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=4) as r: raw=json.load(r)
    queue={k:len(v) if isinstance(v,list) else v for k,v in raw.items()}
except Exception as e: queue={'status':'UNAVAILABLE','error':type(e).__name__}
repos=[]
for path in ('C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION'):
    commands=[]
    for args in (['rev-parse','HEAD'],['branch','--show-current'],['status','--porcelain=v1']):
        p=subprocess.run(['git','-C',path]+args,capture_output=True,text=True,encoding='utf-8',errors='replace')
        commands.append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    repos.append(dict(path=path,commands=commands))
db=sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
db.row_factory=sqlite3.Row
last=[dict(r) for r in db.execute('SELECT id,role,timestamp,finish_reason,tool_name,substr(content,1,900) AS content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 3',('20261017_115944_b2a338',))]
leases=[]
for p in (MG/'leases').glob('*.json'):
    v=json.loads(p.read_text(encoding='utf-8')); leases.append(dict(path=str(p),status=v.get('status'),invocation_id=v.get('invocation_id')))
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protected_comparison=protected,historical_q11_binding=bindings,
    queue_read_only=queue,repositories=repos,last_owner_messages=last,leases=leases,controller_lock_exists=(MG/'locks/controller.lock').exists(),
    caveat='Snapshot only. Historical LIVE_JOBS is not proof of current ownership. No production DB migration/tests or writer transfer performed.')
(OUT/'CONTEXT_RECONCILIATION.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(protected=len(protected),matches=sum(x['match'] for x in protected),different=[x['relative'] for x in protected if not x['match']],q11_bindings=bindings,queue=queue,last_messages=[{k:r[k] for k in ('id','role','finish_reason')} for r in last]),ensure_ascii=True))
