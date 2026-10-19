from pathlib import Path
import datetime,hashlib,json,subprocess,sys
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015');R6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6');RUN=R6.parents[4]
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((OUT/'root-review/C02A_SCOPE_CANDIDATE02.json').read_text());assert audit['ok']
manifest=OUT/'c02a-worker/candidate-02/MANIFEST.json';assert sha(manifest)=='24a488dc50a4ec6af94f8598a67510bf2be8398301cbcb45d22571be0c69d779'
candidate=json.loads(manifest.read_text());assert all(sha(f['source'])==f['sha256'] for f in candidate['files'])
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':'CODEX-C02B1-STAGED-SOURCE-FRESHNESS','old_owner':'/root/motionforge_c02a_coder','old_owner_status':'completed, candidate02 independently APPROVED','next_owner':'/root/motionforge_c02b1_coder','model':'gpt-6-sol','reasoning':'max','controller':rt.controller_status(),'active_leases':rt.leases_status(),'render_quiet':rt.probe_render_quiet(),'files':[],'new_test':str(R6/'tests/test_codex_c02b1_staged_source.py'),'heads':{}}
for p in sorted(set((R6/'scripts').glob('*.py'))|set((R6/'tests').glob('*.py'))):
    rel=p.relative_to(R6).as_posix();b=p.read_bytes();s=OUT/'preimages/c02b1'/rel;assert not s.exists();s.parent.mkdir(parents=True,exist_ok=True);s.write_bytes(b);assert sha(s)==sha(p)
    rec['files'].append({'path':str(p),'relative':rel,'role':'writable' if rel=='scripts/r6_common.py' else 'protected','sha256':sha(p),'bytes':len(b),'lines':len(b.splitlines()),'mtime_ns':p.stat().st_mtime_ns,'snapshot':str(s),'attribution':'external R6 run artifact, untracked by MAIN/INTEGRATION; exact byte snapshot authority'})
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    head=subprocess.run(['git','--no-optional-locks','-C',repo,'rev-parse','HEAD'],capture_output=True,text=True)
    dirty=subprocess.run(['git','--no-optional-locks','-C',repo,'status','--porcelain'],capture_output=True,text=True)
    rec['heads'][repo]={'exit':head.returncode,'head':head.stdout.strip(),'dirty':dirty.stdout.splitlines()}
rec['ok']=not Path(rec['new_test']).exists() and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE','UNKNOWN')
p=OUT/'C02B1_PREFLIGHT.json';assert not p.exists();p.write_text(json.dumps(rec,indent=2),encoding='utf-8');assert rec['ok']
sp=OUT/'PROJECT_STATE.json';old=sp.read_bytes();prior=OUT/'PROJECT_STATE_C02A_APPROVED_PRE_C02B1.json';assert not prior.exists();state=json.loads(old.decode('utf-8-sig'))
state.update(updated_utc=rec['utc'],status='C02A_APPROVED',active_writer=False,root_review='C02A_REVIEW_02.md',candidate_manifest='c02a-worker/candidate-02/MANIFEST.json',checkpoint='c02a-worker/r01/CHECKPOINT-04.json')
state['completed_tasks'].append({'task':'CODEX-C02A-DEPENDENCY-VERIFICATION','verdict':'APPROVED','review':'C02A_REVIEW_02.md','candidate':'c02a-worker/candidate-02/MANIFEST.json','root_probes':'55/55 + 8/8','root_module':'30/30'})
prior.write_text(json.dumps(state,indent=2),encoding='utf-8')
state.update(task=rec['task'],status='C02B1_READY_TO_DISPATCH',owner=rec['next_owner'],task_packet=str(OUT/'TASK_C02B1.md'),checkpoint=p.name,resume_preflight=p.name,next_action='One new GPT-6 Sol Max owner for staged source freshness; self-review then root independent review; no C02B2 or media execution')
state['quota'].update(last_check='QUOTA_C02B1_DISPATCH.json',ordinary_usage_allowed=True,primary_used_percent=53,weekly_used_percent=55)
for obsolete in ('root_baseline_probes','root_candidate_01_probes'):state.pop(obsolete,None)
state['roadmap']=['C02B1 staged-source freshness','C02B2 complete producer capture/settings/reuse','Event/child outcome correctness','Evidence/media corrections after engineering gates','300s pilot independent semantic acceptance','Tool integration and full source after pilot approval']
sp.write_text(json.dumps(state,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'files':len(rec['files']),'writable':sum(f['role']=='writable' for f in rec['files']),'heads':rec['heads'],'preflight':str(p)}))

