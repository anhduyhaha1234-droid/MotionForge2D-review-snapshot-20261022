from pathlib import Path
import hashlib,json,datetime,sqlite3,subprocess,urllib.request
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
EX=BASE/'outputs/motionforge-gemini-handoff-20261017/execution'
G=EX/'submissions/g1-candidate-03'
O=BASE/'outputs/motionforge-g1-review-03-20261019'
S=O/'candidate/task/corrections/identity/r6'
M=json.loads((G/'MANIFEST.json').read_text(encoding='utf-8-sig'))
R=Path(M['files'][0]['path']).parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def cp(a,b):
    data=a.read_bytes();b.parent.mkdir(parents=True,exist_ok=True)
    assert not b.exists(),str(b)
    b.write_bytes(data);return data
rows=[]
for f in M['files']:
    p=Path(f['path']);data=p.read_bytes();assert sha(data)==f['sha256'],str(p)
    dst=S/f['relative'];cp(p,dst)
    rows.append(dict(relative=f['relative'],source=str(p),snapshot=str(dst),expected_sha256=f['sha256'],snapshot_sha256=sha(data),live_sha256=sha(data),live_matches=True,bytes=len(data)))
deps=[]
for p in (G/'dependencies_snapshot').glob('*.py'):
    dst=S/'scripts'/p.name
    data=cp(p,dst)
    live=R/'scripts'/p.name
    if not live.exists() and p.name=='r6_submission_adapter.py':live=EX/'G1-R1'/p.name
    deps.append(dict(source=str(p),snapshot=str(dst),sha256=sha(data),bytes=len(data),authority='submitted dependency snapshot (not listed in top-level manifest)',live=str(live),live_match=live.is_file() and sha(live.read_bytes())==sha(data)))
for p in [R/'tests'/n for n in ['test_codex_c01_review_binding.py','test_codex_c02a_dependency_verification.py','test_codex_c02b1_staged_source.py']]:
    dst=S/'tests'/p.name;data=cp(p,dst);deps.append(dict(source=str(p),snapshot=str(dst),sha256=sha(data),authority='observed live dependency'))
vendor=R.parent/'r5/vendor/cropandstitch_8584b08d'
for p in vendor.rglob('*.py'):
    dst=S.parent/'r5/vendor/cropandstitch_8584b08d'/p.relative_to(vendor);data=cp(p,dst)
    deps.append(dict(source=str(p),snapshot=str(dst),sha256=sha(data),authority='observed pinned vendor'))
cp(R.parents[2]/'chunk_plan.json',S.parents[2]/'chunk_plan.json')
for p in G.rglob('*'):
    if p.is_file():cp(p,O/'submitted_packet'/p.relative_to(G))
for n in ['STATE.json','CHECKPOINT.json','RESUME.md','auto_nudge_watchdog.py','telegram_heartbeat.py','G1-R1/r6_submission_adapter.py']:
    p=EX/n
    if p.is_file():cp(p,O/'observed_execution'/n)
rules=Path('C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md');cp(rules,O/'authority'/rules.name)
ident=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),submission='g1-candidate-03',files=rows,dependencies=deps,authority_sha256=sha(rules.read_bytes()))
(O/'CANDIDATE_IDENTITY.json').write_text(json.dumps(ident,indent=2),encoding='utf-8')
db=sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');db.row_factory=sqlite3.Row
latest=[dict(r) for r in db.execute('SELECT id,role,timestamp,finish_reason,tool_name,substr(content,1,1400) AS content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 5',('20261017_115944_b2a338',))]
status=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),latest_owner_messages=latest)
try:
    with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=5) as r:queue=json.load(r)
    status['queue']={k:len(v) if isinstance(v,list) else v for k,v in queue.items()}
except Exception as e:status['queue_error']=type(e).__name__
status['repositories']=[]
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    a=[]
    for args in [['rev-parse','HEAD'],['branch','--show-current'],['status','--porcelain=v1']]:
        x=subprocess.run(['git','-C',repo]+args,capture_output=True,text=True,encoding='utf-8',errors='replace');a.append(dict(args=args,exit=x.returncode,stdout=x.stdout,stderr=x.stderr))
    status['repositories'].append(dict(path=repo,commands=a))
(O/'CONTEXT_RECONCILIATION.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
print(json.dumps(dict(snapshot=str(S),exact_files=len(rows),deps=len(deps),queue=status.get('queue'),last=[{k:r[k] for k in ['id','role','finish_reason','timestamp']} for r in latest])))
