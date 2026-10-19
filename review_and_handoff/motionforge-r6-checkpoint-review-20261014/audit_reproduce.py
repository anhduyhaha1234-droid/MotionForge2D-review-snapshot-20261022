from pathlib import Path
import datetime, hashlib, json, sqlite3, subprocess, urllib.request, shutil
O=Path(r'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014')
RUN=Path(r'C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
D=RUN/'tasks/MF-DEMO-LONG-01'; R6=D/'corrections/identity5m_20261008/r6'
OLD=Path(r'C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r5-review-20261012')
MAIN=Path(r'C:/Users/Admin/MotionForge2D')
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def meta(p):
    if not p.exists():return {'missing':True}
    z={'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'sha256':digest(p)}
    if p.suffix.lower() in ['.json','.jsonl','.md','.py','.cmd']:z['lines']=len(p.read_bytes().splitlines())
    return z
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def run(args):
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    return {'command':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
def save(name,data):
    p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),p
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    O.mkdir(parents=True,exist_ok=True)
    r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshots':{},'protected':{},'media':{}}
    # New reviewer evidence only; no imports of implementation and no runtime writes.
    roots=[R6/'scripts',R6/'checkpoint',R6/'receipts',R6/'evidence/terminal',R6/'evidence/qa',RUN/'manager/tools',RUN/'manager/evidence/r6']
    files=[]
    for root in roots:
        files += [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ['.py','.json','.jsonl','.md','.cmd']]
    files += [R6/'source_actor_ledger.jsonl', R6/'cast_atlas.json',R6/'event_map.json',R6/'evidence/matrix.json',D/'chunk_plan.json',D/'worker_R6f.log',RUN/'manager/registry/SESSION_REGISTRY.json',RUN/'manager/DISPATCH_LEDGER.jsonl']
    files += list((RUN/'manager').glob('LONG01_receipt_R6*.json')) + list((RUN/'manager/packets').glob('LONG01_R6*.md'))
    for p in sorted(set(files)):
        rel=p.relative_to(RUN);q=O/'snapshot'/rel;q.parent.mkdir(parents=True,exist_ok=True)
        assert not q.exists();shutil.copyfile(p,q)
        a=meta(p);b=meta(q);assert a['sha256']==b['sha256']
        r['snapshots'][str(p)]={**a,'snapshot':str(q)}
    for p in [MAIN/'AGENTS.md',MAIN/'docs/pm/SESSION_PROTOCOL.md',*[MAIN/'docs/pm'/n for n in ['HERMES_AUTOPILOT_RULES.md','CODEX_PM_HANDOFF.md','ROADMAP.md']]]:
        q=O/'preimages'/p.name;q.parent.mkdir(exist_ok=True);assert not q.exists();shutil.copyfile(p,q);r['protected'][str(p)]=meta(p)
    old=read(OLD/'AUDIT_R5.json')
    for s in old['protected']:
        p=Path(s)
        if '/manager/' not in s.replace('\\','/') or any(x in s.replace('\\','/') for x in ['/manager/evidence/r4/','/manager/evidence/r5/']):r['protected'][s]=meta(p)
    r['changed_vs_R5_review_baseline']=[s for s,m in r['protected'].items() if s in old['protected'] and m.get('sha256')!=old['protected'][s].get('sha256')]
    for name,p in {'R6':R6/'outputs/IDENTITY5M_R6_MASTER.mp4','comparison':R6/'outputs/IDENTITY5M_R6_COMPARISON.mp4','R5':R6.parent/'r5/outputs/IDENTITY5M_R5_MASTER.mp4','source':D/'source/source_full.mp4'}.items():
        rr=run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)])
        r['media'][name]={'path':str(p),**meta(p),'probe_command':rr['command'],'probe':json.loads(rr['stdout']) if rr['returncode']==0 else rr}
    for n in ['R6','comparison']:
        r['media'][n]['decode']=run(['ffmpeg','-v','error','-i',r['media'][n]['path'],'-map','0:v','-map','0:a?','-f','null','-'])
    r['receipts']={p.stem:read(p) for p in sorted((RUN/'manager').glob('LONG01_receipt_R6*.json'))}
    terminal=R6/'evidence/terminal/LONG01-R6f-20261012T1820Z-3211.json';t=read(terminal)
    r['terminal']={'path':str(terminal),**meta(terminal),'status':t['status'],'matrix':t['matrix'],'checks':[]}
    for a in t['artifacts']:
        p=Path(a['path']);m=meta(p);r['terminal']['checks'].append({'path':str(p),'kind':a['kind'],'expected':a['sha256'],'actual':m.get('sha256'),'match':a['sha256']==m.get('sha256')})
    db=Path(r'C:/Users/Admin/AppData/Local/hermes/state.db')
    r['db_guard']={'path':str(db),'open_mode':'mode=ro; PRAGMA query_only=ON','before':{'bytes':db.stat().st_size,'mtime_ns':db.stat().st_mtime_ns}}
    r['sessions']={}
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
        c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row
        for sid in ['20261012_002032_daa36c','20261007_234033_cc0b6d']:
            r['sessions'][sid]={'counts':[dict(x) for x in c.execute('SELECT active,compacted,count(*) AS n FROM messages WHERE session_id=? GROUP BY active,compacted',(sid,))],
              'last_messages':[dict(x) for x in c.execute("SELECT id,timestamp,role,substr(content,-5000) AS tail FROM messages WHERE session_id=? AND role IN ('assistant','user') AND length(content)>0 ORDER BY id DESC LIMIT 4",(sid,))]}
    r['db_guard']['after']={'bytes':db.stat().st_size,'mtime_ns':db.stat().st_mtime_ns}
    try:
        with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=5) as f:r['queue']=json.load(f)
    except Exception as e:r['queue']={'unknown':str(e)}
    r['processes']=run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process | Where-Object {($_.Name -match 'python|hermes|ffmpeg|ebsynth') -and ($_.CommandLine -match 'mf-delivery|video14b|hermes|rerender')} | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 3"])
    r['gpu']=run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'])
    r['git']={}
    for p in [MAIN,Path(r'C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION')]:
        r['git'][str(p)]={k:run(['git','--no-optional-locks','-C',str(p),*args]) for k,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain'])]}
    r['leases']={str(p):read(p) for p in (RUN/'manager/leases').glob('*R6*.json')}
    r['heartbeat_last']=json.loads((RUN/'manager/HEARTBEAT.jsonl').read_text(encoding='utf-8').splitlines()[-1])
    r['r6_manifest_exists']=(R6/'R6_MANIFEST.json').exists();r['matrix_evidence_exists']=(R6/'evidence/R6_MATRIX_EVIDENCE.json').exists()
    save('AUDIT.json',r)
    shutil.copyfile(Path(__file__),O/'audit_reproduce.py')
    print(json.dumps({'utc':r['utc'],'snapshots':len(r['snapshots']),'protected':len(r['protected']),'changed':r['changed_vs_R5_review_baseline'],'media':{k:{'sha256':v['sha256'],'bytes':v['bytes'],'streams':[{f:s.get(f) for f in ['codec_type','width','height','r_frame_rate','nb_frames','duration']} for s in v['probe']['streams']],'decode':v.get('decode',{}).get('returncode')} for k,v in r['media'].items()},'terminal_mismatches':[a for a in r['terminal']['checks'] if not a['match']],'queue':r['queue'],'sessions':r['sessions'],'manifest_exists':r['r6_manifest_exists'],'matrix_evidence_exists':r['matrix_evidence_exists']},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
