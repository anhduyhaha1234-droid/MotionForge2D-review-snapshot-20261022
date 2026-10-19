from pathlib import Path
import datetime, hashlib, json, sys, subprocess
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
RUN=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
initial=json.loads((OUT/'C02A_PREFLIGHT.json').read_text(encoding='utf-8-sig'))
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':initial['task'],'owner':'/root/motionforge_c02a_coder','model':'gpt-6-sol','reasoning':'max','owner_tool_status':'errored: usage limit; try again at 9:04 AM','controller':rt.controller_status(),'active_leases':rt.leases_status(),'render_quiet':rt.probe_render_quiet(),'files':[],'unexpected_changes':[],'latest_patch_matches':[]}
latest={}
for p in sorted((OUT/'c02a-worker').glob('PATCH_*.json')):
    r=json.loads(p.read_text(encoding='utf-8-sig'));latest[r['path']]=r
for before in initial['files']:
    p=Path(before['path']);b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
    if h!=before['sha256'] and before['role']=='protected':rec['unexpected_changes'].append(str(p))
    rec['files'].append({'path':str(p),'sha256':h,'bytes':len(b),'lines':len(b.splitlines()),'role':before['role']})
new=Path(initial['new_test']);b=new.read_bytes()
rec['files'].append({'path':str(new),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'lines':len(b.splitlines()),'role':'writable'})
for f in rec['files']:
    if f['path'] in latest:rec['latest_patch_matches'].append({'path':f['path'],'matches':f['sha256']==latest[f['path']]['sha256']})
    if f['role']=='writable':
        p=Path(f['path']);snapshot=OUT/'preimages/c02a-resume-0909'/p.name
        assert not snapshot.exists();snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes(p.read_bytes())
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==f['sha256'];f['snapshot']=str(snapshot)
rec['last_checkpoint']='c02a-worker/CHECKPOINT-01.md'
rec['later_evidence']=['c02a-worker/PATCH_03.json','c02a-worker/PATCH_04.json','c02a-worker/PATCH_05.json','c02a-worker/MICRO_03.txt']
rec['last_test']='MICRO_03: 7 tests, 1 failure deps_sha_bool; not submitted; C01 fixture and consumer integration work remain'
rec['heads']={}
for repo in ['C:/Users/Admin/MotionForge2D','C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION']:
    r=subprocess.run(['git','--no-optional-locks','-C',repo,'rev-parse','HEAD'],capture_output=True,text=True);rec['heads'][repo]={'rc':r.returncode,'head':r.stdout.strip()}
rec['ok']=not rec['unexpected_changes'] and all(x['matches'] for x in rec['latest_patch_matches']) and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE','UNKNOWN')
target=OUT/'RESUME_PREFLIGHT_C02A_20261016T0909.json';assert not target.exists();target.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
state=json.loads((OUT/'PROJECT_STATE.json').read_text(encoding='utf-8-sig'))
state.update(updated_utc=rec['utc'],status='C02A_READY_TO_RESUME_AFTER_QUOTA' if rec['ok'] else 'C02A_BLOCKED_RESUME_PREFLIGHT',active_writer=False,checkpoint=target.name,resume_preflight=target.name,next_action='Resume same C02A owner from PATCH_05/MICRO_03; fix and complete existing packet; no new writer')
state['quota'].update(coder_prior_error='C02A: usage limit; try again at 9:04 AM',last_check='QUOTA_RESUME_20261016T0909.json',ordinary_usage_allowed=True,primary_used_percent=3,weekly_used_percent=32,reset_observed=True)
(OUT/'PROJECT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'files':len(rec['files']),'patches':rec['latest_patch_matches'],'unexpected':rec['unexpected_changes'],'heads':rec['heads'],'receipt':str(target)}))
raise SystemExit(0 if rec['ok'] else 2)
