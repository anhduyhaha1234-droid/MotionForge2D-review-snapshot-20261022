from pathlib import Path
import json, hashlib, datetime, difflib

base=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
out=base/'outputs/motionforge-gemini-handoff-20261017'
old=base/'outputs/motionforge-codex-takeover-20261015'
main=Path('C:/Users/Admin/MotionForge2D')

def sha(b): return hashlib.sha256(b).hexdigest()
def normal(b): return b.decode('utf-8-sig').replace('\r\n','\n')

changes=[]
for name,first_anchor in [('HERMES_AUTOPILOT_RULES.md','### 0.11. Codex coding takeover theo user15/10/2026'),('CODEX_PM_HANDOFF.md','### Codex takeover15/10/2026 — C01, user-authorized'),('ROADMAP.md','### Codex takeover15/10/2026 — C01, user-authorized')]:
    p=main/'docs/pm'/name
    b=(out/'preimages'/name).read_bytes()
    c=p.read_bytes()
    bn,cn=normal(b),normal(c)
    bi,ci=bn.index(first_anchor),cn.index(first_anchor)
    assert bn[bi:]==cn[ci:], 'Historical content changed: '+name
    assert cn[:bi]==bn[:bi], 'Header changed: '+name
    inserted=cn[bi:ci]
    assert inserted and cn==bn[:bi]+inserted+bn[bi:]
    # Retain every pre-existing byte, including the original newline style.
    raw_anchor=first_anchor.encode('utf-8')
    idx=b.index(raw_anchor)
    nl='\r\n' if b.count(b'\r\n') else '\n'
    new=b[:idx]+inserted.replace('\n',nl).encode('utf-8')+b[idx:]
    if new!=c: p.write_bytes(new)
    changes.append({'path':str(p),'before_sha256':sha(b),'after_sha256':sha(new),'inserted_lines':len(inserted.splitlines()),'historical_bytes_unchanged':True})
    (out/(name+'.diff')).write_text(''.join(difflib.unified_diff(bn.splitlines(True),normal(new).splitlines(True),fromfile='before/'+name,tofile='after/'+name)),encoding='utf-8')

sp=old/'PROJECT_STATE.json'
before=(out/'preimages/PROJECT_STATE.json').read_bytes()
state=json.loads(sp.read_text(encoding='utf-8-sig'))
assert state['status']=='PAUSED_BY_USER' and state['active_writer'] is False
assert state['owner']=='/root/motionforge_c02b2_coder'
assert 'prepared_handoff' not in state
state['prepared_handoff']={
    'status':'PREPARED_NOT_DISPATCHED','prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'prompt':str(out/'PROMPT_GEMINI_MOTIONFORGE_VI.md'),
    'starter':str(out/'START_HERE_VI.md'),
    'preflight':str(out/'HANDOFF_PREFLIGHT.json'),
    'planned_model':'ag/gemini-3.8-flash-high','authority':'HERMES_AUTOPILOT_RULES.md section 0.12',
    'activation':'User delivers prompt; fresh ownership/process/queue/lease and current-byte preflight must pass before transfer/writes',
    'automation':'Remain PAUSED; no dispatch or resume performed',
    'root_gates':['G1 engineering before media','G2 pilot before full-source/app integration','G3 final product acceptance']
}
# Preserve every prior state field value; preparation is an additive index only.
assert all(state[k]==v for k,v in json.loads(before.decode('utf-8-sig')).items())
sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
changes.append({'path':str(sp),'before_sha256':sha(before),'after_sha256':sha(sp.read_bytes()),'existing_field_values_unchanged':True})

preflight=json.loads((out/'HANDOFF_PREFLIGHT.json').read_text(encoding='utf-8'))
for f in preflight['current_c02b2_files']:
    assert sha(Path(f['path']).read_bytes())==f['sha256'],'Production file changed unexpectedly'

required=[old/'TASK_C02B2.md',old/'skills/SKILL_SOURCE_LOCK.json',old/'c02b2-worker/v4-replay-03/RESULT.json',old/'C01_REVIEW_02.md',old/'C02A_REVIEW_02.md',old/'C02B1_REVIEW_01.md',main/'docs/PRODUCT_REQUIREMENTS_V2.md',main/'docs/MASTER_PLAN_V1.md',main/'docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md',base/'outputs/motionforge-r6-checkpoint-review-20261014/CORRECTION_MATRIX.md',Path('C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/TECH_CONFORMANCE_MATRIX.md'),base/'outputs/9router-gemini-20261016/FINAL_STATUS.json']
assert all(p.exists() for p in required),[str(p) for p in required if not p.exists()]
automation=Path('C:/Users/Admin/.codex/automations/motionforge-checkpoint-v-quota/automation.toml').read_text(encoding='utf-8')
assert 'status = "PAUSED"' in automation
prompt=(out/'PROMPT_GEMINI_MOTIONFORGE_VI.md').read_text(encoding='utf-8')
assert prompt.startswith('Trước mọi preflight')
assert prompt.count('```')%2==0
for term in ['CHECKPOINT_015','P1','P6','G1','G2','G3','PAUSED','NOT_APPROVED','ag/gemini-3.8-flash-high','UNKNOWN']:
    assert term in prompt,term

manifest={'schema':1,'status':'PREPARED_NOT_DISPATCHED','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pm_changes':changes,'production_files_unchanged':4,'automation_status':'PAUSED','required_reference_paths_verified':len(required),'historical_document_bytes_preserved':True,'no_code_render_owner_transfer_or_model_dispatch':True,'artifacts':[]}
for p in sorted(out.iterdir()):
    if p.is_file() and p.name!='HANDOFF_MANIFEST.json':
        b=p.read_bytes()
        manifest['artifacts'].append({'path':str(p),'bytes':len(b),'sha256':sha(b)})
(out/'HANDOFF_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':manifest['status'],'references_checked':len(required),'prompt_chars':len(prompt),'historical_bytes_preserved':True,'automation':'PAUSED','production_files_unchanged':4,'artifacts':len(manifest['artifacts'])},ensure_ascii=False))
