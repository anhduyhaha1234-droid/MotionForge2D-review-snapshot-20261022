from pathlib import Path
import hashlib,json,datetime,difflib,sqlite3,subprocess,urllib.request
B=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
E=B/'outputs/motionforge-gemini-handoff-20261017/execution'
G=E/'submissions/g1-candidate-04'
O=B/'outputs/motionforge-g1-review-04-20261019'
P=B/'outputs/motionforge-g1-review-03-20261019'
S=O/'candidate/task/corrections/identity/r6'
M=json.loads((G/'MANIFEST.json').read_text(encoding='utf-8-sig'))
R=Path(M['files'][0]['path']).parents[1]
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 assert not b.exists(),str(b)
 b.write_bytes(a.read_bytes())
rows=[];diffs=[]
old=json.loads((P/'submitted_packet/MANIFEST.json').read_text(encoding='utf-8-sig'))
oldmap={Path(f['path']).name:f for f in old['files']}
for f in M['files']:
 p=Path(f['path']); sources=[x for x in (G/'source_snapshot').rglob(p.name) if x.is_file()]
 assert len(sources)==1,(p,sources)
 src=sources[0]; rel=Path('scripts' if p.suffix=='.py' and not p.name.startswith('test_') else 'tests')/p.name
 cp(src,S/rel)
 oldp=P/'candidate/task/corrections/identity/r6'/rel
 prev=sh(oldp) if oldp.is_file() else None
 row=dict(path=str(p),relative=str(rel),submitted_relative=f['relative'],sha256=f['sha256'],live_sha256=sh(p),snapshot_sha256=sh(src),bytes=src.stat().st_size,expected_bytes=f.get('bytes'),previous_sha256=prev,changed=prev!=sh(src))
 rows.append(row)
 if row['changed'] and oldp.is_file():diffs.extend(difflib.unified_diff(oldp.read_text(encoding='utf-8-sig').splitlines(True),src.read_text(encoding='utf-8-sig').splitlines(True),fromfile='03/'+str(rel),tofile='04/'+str(rel)))
deps=[]
for p in (G/'dependencies_snapshot').rglob('*.py'):
 dst=S/'scripts'/p.name
 if dst.exists():
  deps.append(dict(name=p.name,sha256=sh(p),duplicate=True,matches=sh(p)==sh(dst)));continue
 cp(p,dst); oldp=P/'candidate/task/corrections/identity/r6/scripts'/p.name
 deps.append(dict(name=p.name,sha256=sh(p),changed=not oldp.exists() or sh(p)!=sh(oldp),live_match=(R/'scripts'/p.name).exists() and sh(p)==sh(R/'scripts'/p.name)))
for n in ['test_codex_c01_review_binding.py','test_codex_c02a_dependency_verification.py','test_codex_c02b1_staged_source.py']:
 cp(R/'tests'/n,S/'tests'/n)
for p in (R.parent/'r5/vendor/cropandstitch_8584b08d').rglob('*.py'):cp(p,S.parent/'r5/vendor/cropandstitch_8584b08d'/p.relative_to(R.parent/'r5/vendor/cropandstitch_8584b08d'))
cp(R.parents[2]/'chunk_plan.json',S.parents[2]/'chunk_plan.json')
for p in G.rglob('*'):
 if p.is_file():cp(p,O/'submitted_packet'/p.relative_to(G))
for n in ['STATE.json','CHECKPOINT.json','RESUME.md','auto_nudge_watchdog.py','telegram_heartbeat.py']:
 if (E/n).is_file():cp(E/n,O/'observed_execution'/n)
rules=Path('C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md');cp(rules,O/'authority'/rules.name)
identity=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,dependencies=deps,rules_sha256=sh(rules))
(O/'CANDIDATE_IDENTITY.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
(O/'DELTA_03_04.patch').write_text(''.join(diffs),encoding='utf-8')
context={}
db=sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');db.row_factory=sqlite3.Row
context['owner_messages']=[dict(r) for r in db.execute('SELECT id,role,timestamp,finish_reason,tool_name,substr(content,1,500) AS content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 3',('20261017_115944_b2a338',))];db.close()
try:
 with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=5) as resp:q=json.load(resp)
 context['queue']={k:len(v) if isinstance(v,list) else v for k,v in q.items()}
except Exception as ex:context['queue_error']=type(ex).__name__
context['repositories']=[]
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
 commands=[]
 for args in [['rev-parse','HEAD'],['branch','--show-current'],['status','--porcelain=v1']]:
  v=subprocess.run(['git','-C',repo]+args,capture_output=True,text=True,encoding='utf-8',errors='replace');commands.append(dict(args=args,exit=v.returncode,stdout=v.stdout,stderr=v.stderr))
 context['repositories'].append(dict(path=repo,commands=commands))
(O/'CONTEXT_RECONCILIATION.json').write_text(json.dumps(context,indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(rows),all_hashes_match=all(r['sha256']==r['live_sha256']==r['snapshot_sha256'] for r in rows),changed=[r['relative'] for r in rows if r['changed']],dependencies=deps,queue=context.get('queue'),last_owner=[{k:r[k] for k in ['id','role','timestamp','finish_reason']} for r in context['owner_messages']],rules_sha256=sh(rules)),indent=2))
