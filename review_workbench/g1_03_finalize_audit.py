from pathlib import Path
import json,hashlib,datetime,ast,sqlite3,subprocess,shutil,importlib.metadata as meta
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2');O=BASE/'outputs/motionforge-g1-review-03-20261019';OLD=BASE/'outputs/motionforge-g1-review-02-20261018';R=O/'candidate/task/corrections/identity/r6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
    p=O/n;p.parent.mkdir(exist_ok=True,parents=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
ident=json.loads((O/'CANDIDATE_IDENTITY.json').read_text());checks=[];delta=[]
for x in ident['files']:
    p=Path(x['source']);s=Path(x['snapshot']);checks.append({'relative':x['relative'],'expected':x['expected_sha256'],'live':sha(p),'snapshot':sha(s)})
    old=OLD/'candidate/task/corrections/identity/r6'/x['relative'];delta.append({'relative':x['relative'],'candidate02_sha256':sha(old) if old.exists() else None,'candidate03_sha256':sha(s),'changed_since02':not old.exists() or sha(old)!=sha(s)})
save('POST_REVIEW_HASH_CHECK.json',checks);save('DELTA_VS_CANDIDATE02.json',delta)
versions={n:meta.version(n) for n in ['Pillow','pydantic','numpy','torch','filelock']}
ff=subprocess.run(['ffprobe','-version'],capture_output=True,text=True);versions['ffprobe']=ff.stdout.splitlines()[0]
for n in ['ruff','pyflakes']:
    try:versions[n]=meta.version(n)
    except meta.PackageNotFoundError:versions[n]='not installed in review runtime'
nodes=[]
for p in (R/'tests').glob('*.py'):
    tree=ast.parse(p.read_text(encoding='utf-8-sig'));nodes.extend(f'{p.name}::{n.name}' for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
save('TEST_SCOPE.json',{'runtime':versions,'collected_AST_not_execution':nodes,'count':len(nodes),'root_broad89_executed':False,'reason':'Risk-critical micro failures block broad final gate. Asset-focused10/10 independently executed; root probes are separate controls, not a forged broad count.'})
mg=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager')
race=json.loads((mg/'evidence/r6/q11/Q11_R6_RACE_RESULTS.json').read_text());h=mg/'evidence/r6/Q11_R6_HARNESS_TEST_RESULTS.json';hd=json.loads(h.read_text());bind=[]
for n,k in [('dispatch_long.py','dispatch_sha256'),('invocation_runtime.py','invocation_runtime_sha256'),('terminal_contract.py','terminal_contract_sha256')]:bind.append({'file':str(mg/'tools'/n),'current_sha':sha(mg/'tools'/n),'race_provenance_sha':race['provenance'][k],'match':sha(mg/'tools'/n)==race['provenance'][k]})
save('Q11_BINDING_AUDIT.json',{'race_passed':race['passed'],'production_bindings':bind,'harness51':{'path':str(h),'sha256':sha(h),'top_keys':list(hd),'passed':hd.get('passed'),'total':hd.get('total'),'case_names':[r['name'] for r in hd.get('results',[])],'limitation':'Candidate03 test checks passed==51 and3production hashes; complete runtime/test/source provenance and lifecycle coverage mapping not supplied. Do not count toy O_EXCL as production controller race.'}})
for p in [h,mg/'evidence/r6/q11/Q11_R6_RACE_RESULTS.json']:
    dst=O/'observed_manager'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
v=O/'vision';direct=json.loads((v/'DIRECT_IMAGE_RECEIPT.json').read_text());helper=json.loads((v/'HELPER_LIVE_RECEIPT.json').read_text());expected=direct['expected'];checksvision={k:helper['analysis_json'].get(k)==value for k,value in expected.items()}
config=Path('C:/Users/Admin/AppData/Local/hermes/config.yaml')
with sqlite3.connect('file:C:/Users/Admin/AppData/Roaming/9router/db/data.sqlite?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    usage=[dict(r) for r in db.execute('SELECT id,timestamp,provider,model,status,promptTokens,completionTokens FROM usageHistory WHERE id>=? AND provider=? ORDER BY id',(64367,'antigravity'))]
save('vision/VERIFICATION.json',{'direct_image':'PASS 7/7','installed_helper_image_checks':checksvision,'helper_pass':all(checksvision.values()),'native_Hermes_tool_envelope_test':'INCOMPLETE: one request timed out after90s; no capability override applied; does not prove model lacks vision','config_sha256':sha(config),'config_unchanged':sha(config)=='442333a3092b6349f54aaae495e7bed0b6b7fc15ffe87c653b3a2b867a2feb05','native_video_audio':'UNVERIFIED; helper accepts sampled frames only','usage_observed_not_all_attributed_to_review':usage,'main_session_dispatched':False,'fallback':False})
save('vision/NATIVE_TOOL_TIMEOUT.json',{'script':str(BASE/'work/vision-g1c03/hermes_tool_smoke.py'),'result':'TimeoutError waiting for /v1/chat/completions response after90s','local_steps_completed':['candidate per-model capability loaded in isolated process','vision_analyze produced multimodal envelope','AIAgent unwrapped image tool content'],'HTTP_request_shape':'user + assistant tool_call + tool message containing image parts; model ag/gemini-3.8-flash-high','limitation':'No server cancellation proof and no received model answer. No automatic retry, no global override installed.'})
for name in ['g1_03_event_controls.py','g1_03_propagate_boundaries.py','g1_03_finalize_audit.py']:
    shutil.copyfile(BASE/'work'/name,O/name)
save('FINAL_AUDIT.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exact_manifest_files':len(checks),'live_match':sum(x['expected']==x['live'] for x in checks),'snapshot_match':sum(x['expected']==x['snapshot'] for x in checks),'changed_since_candidate02':[x['relative'] for x in delta if x['changed_since02']],'root_production_patches':0,'root_new_GPU_jobs':0,'config_unchanged':sha(config)=='442333a3092b6349f54aaae495e7bed0b6b7fc15ffe87c653b3a2b867a2feb05','vision_helper_pass':all(checksvision.values()),'subagent_limit':'Both read-only helpers reached usage limit; no replacement/fallback launched. Retained completed evidence.'})
print(json.dumps({'live_matches':sum(x['expected']==x['live'] for x in checks),'manifest_files':len(checks),'changed_since02':sum(x['changed_since02'] for x in delta),'helper_checks':checksvision,'config_unchanged':sha(config)=='442333a3092b6349f54aaae495e7bed0b6b7fc15ffe87c653b3a2b867a2feb05','usage':usage[-5:]}))
