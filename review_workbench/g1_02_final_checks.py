from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess,datetime,time,importlib,ast
from unittest.mock import patch
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-02-20261018'
R6=OUT/'candidate/task/corrections/identity/r6'
WORK=BASE/'work/g1-review-02-fixtures'
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',CUDA_VISIBLE_DEVICES='-1')
for v in ('C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR'): env[v]=str(WORK)
os.environ.update(env);sys.path.insert(0,str(R6/'tests'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    p=OUT/name;assert not p.exists();p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args,cwd=None):
    start=time.monotonic();at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    r=subprocess.run(args,env=env,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=50)
    return dict(command=args,cwd=str(cwd),at_utc=at,duration_seconds=time.monotonic()-start,exit=r.returncode,stdout=r.stdout,stderr=r.stderr)

# Reproduction of historical terminal path is confined to a cloned fixture.
root=WORK/'terminal/task/corrections/identity/r6';root.mkdir(parents=True)
shutil.copytree(R6/'scripts',root/'scripts')
shutil.copyfile(R6.parents[2]/'chunk_plan.json',root.parents[2]/'chunk_plan.json')
(root/'evidence').mkdir();(root/'evidence/matrix.json').write_text(json.dumps({'rows':{f'Q{i:02d}':'PASS' for i in range(1,13)}}))
r=run([sys.executable,'-B',str(root/'scripts/write_terminal_record_r6g.py'),'--submitted'])
r['published_terminal']=[json.loads(p.read_text(encoding='utf-8')) for p in (root/'evidence/terminal').glob('*.json')]
r['scope']='Observed unchanged historical dependency, NOT one of candidate15; fixture clone only. New candidate builder did not demonstrate a replacement submission consumer.'
save('TERMINAL_CALLER_PROBE.json',r)
print(json.dumps({'terminal_exit':r['exit'],'published_status':[x['status'] for x in r['published_terminal']],'tail':r['stdout'][-500:]}))

a3=importlib.import_module('test_gemini_a3_event_tracking');f=a3.EventTimingAndTrackingTests();f.setUp()
try:
    led=importlib.import_module('r6_ledger');keygen=importlib.import_module('r6_keygen')
    f.k.SHOTS=['S0021'];f.k.PLAN={'S0021':{'start_frame':0,'frames':60}}
    led.R3_LEDGER=f.root/'source_ledger.json';led.R5_SB=f.root/'old_storyboard';led.R5_SB.mkdir()
    led.R3_LEDGER.write_text(json.dumps({'shots':{'S0021':{'src':[0,60],'actors':[{'entity':'E1'}],'events':[{'frame':43}],'contacts':[{'from':9,'to':29}]}}}))
    (led.R5_SB/'S0021.json').write_text(json.dumps({'keys':[{'fid':1},{'fid':60}]}))
    led.OVR={'S0021':{'actors':{'E1':[(1,19,'VISIBLE'),(20,29,'FULLY_OCCLUDED'),(30,49,'VISIBLE'),(50,60,'NOT_PRESENT')]}}}
    led.main();board=json.loads((f.k.R6/'storyboard/S0021.json').read_text());calls=[]
    with patch.object(keygen,'run_key',side_effect=lambda sid,fid:calls.append(fid)),patch.object(sys,'argv',['r6_keygen.py','S0021']):keygen.main()
    with patch.object(f.propagate.G,'gate_key',return_value=True):g=f.propagate.G.gate_shot_before_propagate('S0021')
    record={'board_fids':[k['fid'] for k in board['keys']],'actual_keygen_discovery':calls,'gate':g,'propagation_discovery':f.propagate.build_key_fids('S0021',60),'stub_boundaries':'run_key image generation and per-key semantic reviews stubbed; actual ledger/main/board/CLI discovery/gate event requirement/build_key_fids preserved.'}
    save('EVENT_CALL_PATH_CONTROL.json',record);print(json.dumps(record))
finally:f.doCleanups()

# Evidence structure comparison with installed validation, no production adoption.
from pydantic import BaseModel,ConfigDict,StrictStr,ValidationError
class DependencyEnvelope(BaseModel):
    model_config=ConfigDict(strict=True,extra='forbid')
    kind:StrictStr
    shot:StrictStr
    deps_sha:StrictStr
    consumed:dict
fake={'kind':'r6_key_deps_v4_asset','padding':'x'*70}
try:DependencyEnvelope.model_validate(fake);schema_result='accepted'
except ValidationError as e:schema_result={'rejected':True,'errors':[{'type':x['type'],'loc':x['loc']} for x in e.errors()]}
save('REUSE_SCHEMA_COMPARISON.json',{'fixture':fake,'candidate_matrix_Q07':'PASS (ROOT_PROBES matrix_fake_evidence)','installed_pydantic_2_13_5_prototype':schema_result,'limit':'Evidence of structural rejection only; custom hash/role/invocation/semantic validation still required. No production code adopted.'})

# Inventory and test coverage, not a broad test execution while matrix is open.
import importlib.metadata as meta
vers={}
for n in ('pydantic','numpy','torch','filelock','Pillow','ruff','jsonschema'):
    try:vers[n]=meta.version(n)
    except meta.PackageNotFoundError:vers[n]='NOT_INSTALLED_IN_RUNTIME'
ff=run(['ffprobe','-version']);vers['ffprobe']=ff['stdout'].splitlines()[:1];vers['python']=sys.version
tree=ast.parse((R6/'tests/test_g1_r1_correction.py').read_text(encoding='utf-8'))
tests=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
save('RUNTIME_AND_TEST_SCOPE.json',{'versions':vers,'new_test_names':tests,'count':len(tests),'root_suite89_executed':False,'reason':'Risk-critical micro probes already demonstrate open matrix rows; per rules no broad final gate until closure. 89/89 remains submitted claim, not independently reproduced in this review.'})
ident=json.loads((OUT/'CANDIDATE_IDENTITY.json').read_text(encoding='utf-8'))
checks=[]
manifest=json.loads((OUT/'submitted_packet/MANIFEST.json').read_text(encoding='utf-8'))
for x in ident['files']:
    live=Path(next(y['path'] for y in manifest['files'] if y['relative']==x['relative']))
    checks.append({'relative':x['relative'],'expected':x['expected_sha256'],'snapshot':sha(Path(x['snapshot'])),'live':sha(live)})
save('POST_REVIEW_HASH_CHECK.json',checks)
print(json.dumps({'new_tests_collected':len(tests),'snapshot_matches':sum(r['snapshot']==r['expected'] for r in checks),'live_matches':sum(r['live']==r['expected'] for r in checks),'versions':vers}))
for name in ('g1_02_prepare.py','g1_02_context.py','g1_02_probes.py','g1_02_final_checks.py'):
    shutil.copyfile(BASE/'work'/name,OUT/name)
