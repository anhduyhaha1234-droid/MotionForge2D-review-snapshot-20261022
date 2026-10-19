from pathlib import Path
import datetime, hashlib, json, sys, subprocess, difflib
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
RUN=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
sha=lambda b:hashlib.sha256(b).hexdigest()
pre=json.loads((OUT/'C02A_PREFLIGHT.json').read_text(encoding='utf-8-sig'))
candidate=json.loads((OUT/'c02a-worker/candidate-01/MANIFEST.json').read_text())
snapshot=OUT/'preimages/c02a-r01-resume-1412'
snapshot.mkdir(exist_ok=False)
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':pre['task'],'owner':'/root/motionforge_c02a_coder','model':'gpt-6-sol','reasoning':'max','owner_tool_status':'errored: usage limit; try again at 2:08 PM','controller':rt.controller_status(),'active_leases':rt.leases_status(),'render_quiet':rt.probe_render_quiet(),'files':[],'unexpected_changes':[]}
for f in pre['files']:
    if f['role']=='protected':
        p=Path(f['path']);b=p.read_bytes()
        if sha(b)!=f['sha256']:rec['unexpected_changes'].append(str(p))
        rec['files'].append({'path':str(p),'sha256':sha(b),'bytes':len(b),'lines':len(b.splitlines()),'role':'protected'})
for f in candidate['files']:
    p=Path(f['source']);b=p.read_bytes();s=snapshot/p.name;s.write_bytes(b);assert sha(s.read_bytes())==sha(b)
    changed=sha(b)!=f['sha256']
    if changed and p.name not in ('r6_cache.py','test_codex_c02a_dependency_verification.py'):rec['unexpected_changes'].append(str(p))
    diff=''.join(difflib.unified_diff(Path(f['snapshot']).read_text().splitlines(True),p.read_text().splitlines(True),fromfile=f['snapshot'],tofile=str(p)))
    if diff:(snapshot/(p.name+'.diff')).write_text(diff,encoding='utf-8')
    rec['files'].append({'path':str(p),'sha256':sha(b),'bytes':len(b),'lines':len(b.splitlines()),'mtime_ns':p.stat().st_mtime_ns,'role':'writable','snapshot':str(s),'changed_since_candidate01':changed})
rec['heads']={}
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    r=subprocess.run(['git','--no-optional-locks','-C',repo,'rev-parse','HEAD'],capture_output=True,text=True)
    d=subprocess.run(['git','--no-optional-locks','-C',repo,'status','--porcelain'],capture_output=True,text=True)
    rec['heads'][repo]={'rc':r.returncode,'head':r.stdout.strip(),'dirty':d.stdout.splitlines()}
rec['last_checkpoint']='c02a-worker/r01/CHECKPOINT-00.json'
rec['last_test']='NESTING_RED.txt: 2 tests, 5 errors (RecursionError); raw log preserved. Root nesting red 4/8. R01 unsubmitted.'
rec['decision']='Preserve all partial bytes and continue existing R01 with same owner. Any unreceipted in-scope patch must be reconciled by owner before more edits; no rollback/rebuild.'
rec['quota_receipt']='QUOTA_RESUME_20261016T1412.json'
rec['ok']=not rec['unexpected_changes'] and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE','UNKNOWN')
target=OUT/'RESUME_PREFLIGHT_C02A_R01_20261016T1412.json';assert not target.exists();target.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
sp=OUT/'PROJECT_STATE.json';old=sp.read_bytes();(snapshot/'PROJECT_STATE.before.json').write_bytes(old);state=json.loads(old.decode('utf-8-sig'))
state.update(updated_utc=rec['utc'],status='C02A_R01_READY_TO_RESUME_AFTER_QUOTA' if rec['ok'] else 'C02A_R01_BLOCKED_PREFLIGHT',active_writer=False,checkpoint=target.name,resume_preflight=target.name,next_action=rec['decision'])
state['quota'].update(coder_prior_error='C02A-R01: usage limit; try again at 2:08 PM',last_check=rec['quota_receipt'],ordinary_usage_allowed=True,primary_used_percent=4,weekly_used_percent=48,reset_observed=True)
sp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'changed':[{'path':f['path'],'sha256':f['sha256'],'bytes':f['bytes'],'lines':f['lines']} for f in rec['files'] if f.get('changed_since_candidate01')],'unexpected':rec['unexpected_changes'],'controller':rec['controller'],'active_leases':rec['active_leases'],'render_quiet':rec['render_quiet'],'receipt':str(target)}))
raise SystemExit(0 if rec['ok'] else 2)

