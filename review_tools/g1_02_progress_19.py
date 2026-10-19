from pathlib import Path
import json,hashlib,sqlite3,datetime,urllib.request,subprocess,collections
B=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
O=B/'outputs/motionforge-g1-review-02-20261018';E=B/'outputs/motionforge-gemini-handoff-20261017/execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((E/'submissions/g1-candidate-02/MANIFEST.json').read_text())
checks=[{'relative':x['relative'],'submitted':x['sha256'],'current':sha(Path(x['path'])),'mtime_utc':datetime.datetime.fromtimestamp(Path(x['path']).stat().st_mtime,datetime.timezone.utc).isoformat()} for x in m['files']]
old=json.loads((E/'submissions/g1-candidate-01/MANIFEST.json').read_text());a={x['relative']:x['sha256'] for x in old['files']}
changes=[x['relative'] for x in m['files'] if x['sha256']!=a.get(x['relative'])]
state=json.loads((E/'STATE.json').read_text(encoding='utf-8'))
R6=Path(m['files'][0]['path']).parents[1]
shots=state['b1_hard_excerpts']['completed_shots'];media=[]
for sid in shots:
    p=R6/'work'/sid/'blend_manifest.json';rec={'shot':sid,'manifest_exists':p.exists()}
    if p.exists():
        x=json.loads(p.read_text());bd=Path(x.get('blend_dir',''));fs=list(bd.glob('*.jpg'))
        rec.update(manifest_sha=sha(p),manifest_mtime_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),claimed_frames=len(x.get('frames',[])),disk_frames=len(fs),blend_dir=str(bd),last_frame_write_utc=datetime.datetime.fromtimestamp(max((f.stat().st_mtime for f in fs),default=0),datetime.timezone.utc).isoformat())
    media.append(rec)
masters=[]
for p in R6.rglob('*.mp4'):
    if any(t in p.name.lower() for t in ('master','comparison','pilot')):
        masters.append({'path':str(p),'bytes':p.stat().st_size,'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()})
queue={}
try:
    with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=4) as r:q=json.load(r)
    queue={k:len(v) if isinstance(v,list) else v for k,v in q.items()}
except Exception as e:queue={'error':str(e)}
c=sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row
since=datetime.datetime.fromisoformat('2026-10-18T06:47:00+00:00').timestamp()
query='SELECT id,role,timestamp,content,tool_name,finish_reason FROM messages WHERE session_id=? AND timestamp>=? ORDER BY id'
rows=[dict(x) for x in c.execute(query,('20261017_115944_b2a338',since))]
auto=[x for x in rows if x['role']=='user' and (x.get('content')or'').strip()=='tiếp tục làm việc đi']
touches=[x for x in rows if x['role']=='tool' and 'STATE.json touched' in (x.get('content')or'')]
latest=[{**x,'content':x['content'][:1600] if x['content'] else ''} for x in rows[-10:]]
v={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_checks':checks,'changes_vs_candidate01':changes,'new_candidates':[p.name for p in (E/'submissions').iterdir() if p.is_dir()],'b1_frame_inventory':media,'media_claim_caveat':'Count/mtime and manifest hash only; no new visual/audio/semantic approval.','master_inventory':sorted(masters,key=lambda x:x['mtime_utc'],reverse=True)[:12],'queue':queue,'owner_query':query,'owner_query_parameters':['20261017_115944_b2a338',since],'messages_since_prior_review_start':len(rows),'auto_nudges':len(auto),'state_touch_tool_results':len(touches),'roles':dict(collections.Counter(x['role'] for x in rows)),'latest_messages':latest,'current_state':state}
(O/'PROGRESS_AUDIT_20261019.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'observed_execution/STATE_20261019.json').write_bytes((E/'STATE.json').read_bytes())
print(json.dumps({k:v[k] for k in ('observed_utc','changes_vs_candidate01','new_candidates','queue','messages_since_prior_review_start','auto_nudges','state_touch_tool_results','master_inventory')}))
print(json.dumps({'matches':sum(x['current']==x['submitted'] for x in checks),'b1_disk_frames':sum(x.get('disk_frames',0) for x in media),'b1_last_write':max(x.get('last_frame_write_utc','') for x in media),'latest_owner_id':rows[-1]['id']}))
