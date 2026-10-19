from pathlib import Path
import json,hashlib,datetime,subprocess,sqlite3,urllib.request,shutil
O=Path(r'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
RUN=Path(r'C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
D=RUN/'tasks/MF-DEMO-LONG-01';R6=D/'corrections/identity5m_20261008/r6'
M=Path(r'C:/Users/Admin/MotionForge2D')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def meta(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'lines':len(p.read_bytes().splitlines()) if p.suffix in ['.py','.md','.json','.jsonl'] else None,'mtime_ns':p.stat().st_mtime_ns}
def cmd(args):
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace');return {'args':args,'rc':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
def main():
 O.mkdir(parents=True,exist_ok=True)
 r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'user_authority':'2026-10-15 user requests Codex coding sub-agent and independent review; confirms gpt-6-sol max; supersedes no-Codex-writer restriction only within scoped handoff','preimages':{},'media':{},'git':{}}
 paths=list((R6/'scripts').glob('*.py'))+list((R6/'tests').glob('*.py'))
 paths += [M/'docs/pm'/n for n in ['HERMES_AUTOPILOT_RULES.md','CODEX_PM_HANDOFF.md','ROADMAP.md']]
 paths += [RUN/'manager/registry/SESSION_REGISTRY.json',RUN/'manager/LONG01_receipt_R6g.json',RUN/'manager/packets/LONG01_R6g.md']
 for p in paths:
  if not p.exists():continue
  root=RUN if p.is_relative_to(RUN) else M
  q=O/'preimages'/('run' if root==RUN else 'main')/p.relative_to(root)
  q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(p,q)
  r['preimages'][str(p)]={**meta(p),'snapshot':str(q),'snapshot_sha256':sha(q)}
 for p in [M,Path(r'C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION')]:
  r['git'][str(p)]={k:cmd(['git','--no-optional-locks','-C',str(p),*v]) for k,v in {'head':['rev-parse','HEAD'],'branch':['branch','--show-current'],'status':['status','--porcelain']}.items()}
 r['processes']=cmd(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process | Where-Object {($_.Name -match 'python|hermes|ffmpeg|ebsynth') -and ($_.CommandLine -match 'mf-delivery|video14b|hermes')} | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 3"])
 try:
  with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=5) as f:r['queue']=json.load(f)
 except Exception as e:r['queue']={'unknown':str(e)}
 r['leases']={p.name:json.loads(p.read_text(encoding='utf-8')) for p in (RUN/'manager/leases').glob('*R6g*.json')}
 r['heartbeat_last']=json.loads((RUN/'manager/HEARTBEAT.jsonl').read_text(encoding='utf-8').splitlines()[-1])
 r['sessions']={}
 db=Path(r'C:/Users/Admin/AppData/Local/hermes/state.db')
 with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
  c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row
  for sid in ['20261012_002032_daa36c','20261007_234033_cc0b6d']:
   r['sessions'][sid]={'counts':[dict(x) for x in c.execute('SELECT active,compacted,count(*) AS n FROM messages WHERE session_id=? GROUP BY active,compacted',(sid,))], 'last':[dict(x) for x in c.execute("SELECT id,timestamp,role,substr(content,-3000) AS tail FROM messages WHERE session_id=? AND role IN ('assistant','user') AND length(content)>0 ORDER BY id DESC LIMIT 2",(sid,))]}
 for n,p in {'R6f_master':R6/'outputs/IDENTITY5M_R6_MASTER.mp4','R6f_comparison':R6/'outputs/IDENTITY5M_R6_COMPARISON.mp4','source':D/'source/source_full.mp4'}.items():r['media'][n]={'path':str(p),**meta(p)}
 dest=O/'PREFLIGHT.json';assert not dest.exists();dest.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 shutil.copyfile(Path(__file__),O/Path(__file__).name)
 print(json.dumps({'utc':r['utc'],'preimages':len(r['preimages']),'queue':r['queue'],'leases':r['leases'],'heartbeat':r['heartbeat_last'],'sessions':r['sessions']},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
