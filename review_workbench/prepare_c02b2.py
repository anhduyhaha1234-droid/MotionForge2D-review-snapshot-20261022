from pathlib import Path
import datetime,hashlib,json,subprocess,sys
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015');R6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6');RUN=R6.parents[4]
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((OUT/'root-review/C02B1_RECONCILIATION_20261016T1917.json').read_text())['ok']
m=json.loads((OUT/'c02b1-worker/candidate-01/MANIFEST.json').read_text())
assert all(sha(f['live']['path'])==f['live']['sha256'] for f in m['files'].values())
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':'CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE','old_owner':'/root/motionforge_c02b1_coder','old_owner_status':'completed, independently APPROVED','next_owner':'/root/motionforge_c02b2_coder','model':'gpt-6-sol','reasoning':'max','controller':rt.controller_status(),'active_leases':rt.leases_status(),'render_quiet':rt.probe_render_quiet(),'files':[],'new_files':[str(R6/'scripts/r6_key_recipe.py'),str(R6/'tests/test_codex_c02b2_per_actor_reuse.py')],'heads':{}}
for p in sorted(set((R6/'scripts').glob('*.py'))|set((R6/'tests').glob('*.py'))):
    rel=p.relative_to(R6).as_posix();b=p.read_bytes();s=OUT/'preimages/c02b2'/rel;assert not s.exists();s.parent.mkdir(parents=True,exist_ok=True);s.write_bytes(b);assert sha(s)==sha(p)
    rec['files'].append({'path':str(p),'relative':rel,'role':'writable' if rel in ('scripts/r6_cache.py','scripts/r6_keygen.py') else 'protected','sha256':sha(p),'bytes':len(b),'lines':len(b.splitlines()),'mtime_ns':p.stat().st_mtime_ns,'snapshot':str(s),'attribution':'external R6 run artifact; exact snapshot authority, not tracked by MAIN/INTEGRATION'})
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    h=subprocess.run(['git','--no-optional-locks','-C',repo,'rev-parse','HEAD'],capture_output=True,text=True)
    d=subprocess.run(['git','--no-optional-locks','-C',repo,'status','--porcelain'],capture_output=True,text=True)
    rec['heads'][repo]={'exit':h.returncode,'head':h.stdout.strip(),'dirty':d.stdout.splitlines()}
rec['ok']=not any(Path(p).exists() for p in rec['new_files']) and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE','UNKNOWN')
p=OUT/'C02B2_PREFLIGHT.json';assert not p.exists();p.write_text(json.dumps(rec,indent=2),encoding='utf-8');assert rec['ok']
sp=OUT/'PROJECT_STATE.json';b=sp.read_bytes();previous=OUT/'PROJECT_STATE_C02B1_APPROVED_PRE_C02B2.json';assert not previous.exists();previous.write_bytes(b)
state=json.loads(b.decode('utf-8-sig'));state.update(updated_utc=rec['utc'],task=rec['task'],owner=rec['next_owner'],status='C02B2_READY_TO_DISPATCH',active_writer=False,task_packet=str(OUT/'TASK_C02B2.md'),checkpoint=p.name,resume_preflight=p.name,next_action='One new GPT-6 Sol Max writer implements per-actor complete verified reuse; self-review then root review')
state['roadmap']=['C02B2 per-actor complete verified reuse','C02B3 asset producer provenance/reuse and legacy-media gate decision','Event/child outcome correctness','Evidence/media correction after engineering gates','300s pilot semantic acceptance','Tool integration and full source after pilot approval']
sp.write_text(json.dumps(state,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'files':len(rec['files']),'writable':sum(f['role']=='writable' for f in rec['files']),'new_files':rec['new_files'],'heads':{p:r['head'] for p,r in rec['heads'].items()},'receipt':str(p)}))

