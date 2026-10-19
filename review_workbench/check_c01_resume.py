from pathlib import Path
import sys, json, hashlib, datetime, subprocess
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
RUN=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'/root/motionforge_c01_coder','owner_tool_status':'errored usage limit; no active agent','model':'gpt-6-sol','reasoning':'max','prior_error':'Usage limit, retry at 3:03 AM; observed before heartbeat resume','quota_api':'QUOTA_RESUME_20261016T0405.json','controller':rt.controller_status(),'active_leases':rt.leases_status(),'render_quiet':rt.probe_render_quiet(),'candidate_files':[]}
for f in json.loads((OUT/'c01-worker/CANDIDATE_MANIFEST_FINAL.json').read_text())['files']:
    p=Path(f['path']); b=p.read_bytes(); sha=hashlib.sha256(b).hexdigest()
    rec['candidate_files'].append({'path':str(p),'sha256':sha,'bytes':len(b),'unchanged':sha.lower()==f['sha256'].lower()})
heads={}
for p in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    r=subprocess.run(['git','--no-optional-locks','-C',p,'rev-parse','HEAD'],capture_output=True,text=True)
    heads[p]={'rc':r.returncode,'head':r.stdout.strip()}
rec['heads']=heads
rec['ok']=all(f['unchanged'] for f in rec['candidate_files']) and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE','UNKNOWN') and all(x['rc']==0 for x in heads.values())
p=OUT/'RESUME_PREFLIGHT_20261016T0405.json'; assert not p.exists()
p.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
state=json.loads((OUT/'PROJECT_STATE.json').read_text(encoding='utf-8'))
state.update(updated_utc=rec['utc'],status='READY_TO_RESUME_C01_R01' if rec['ok'] else 'BLOCKED_RESUME_PREFLIGHT',active_writer=False,checkpoint='c01-worker/CHECKPOINT_03.json',next_action='Resume exact coder for C01-R01 after quota reset; no new owner',resume_preflight=p.name)
state['quota'].update(coder_prior_error=rec['prior_error'],last_check='QUOTA_RESUME_20261016T0405.json',ordinary_usage_allowed=True,primary_used_percent=0,weekly_used_percent=16,reset_observed=True)
(OUT/'PROJECT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rec,ensure_ascii=False))
if not rec['ok']: raise SystemExit(2)
