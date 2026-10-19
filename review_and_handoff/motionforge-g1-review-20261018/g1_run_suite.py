from pathlib import Path
import os,sys,json,subprocess,datetime,time,hashlib,shutil
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-20261018'
R6=OUT/'candidate/task/corrections/identity/r6'
WORK=BASE/'work/g1-review-fixtures'
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',CUDA_VISIBLE_DEVICES='-1')
for v in ('C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR'):
    env[v]=str(WORK)
driver=WORK/'propagate_cli_driver.py'
original=driver.read_text(encoding='utf-8')
fixed=WORK/'propagate_cli_driver_v2.py'
fixed.write_text(original.replace('p.blend_script=lambda: Path(sys.argv[3])','fixture_child=Path(sys.argv[3])\np.blend_script=lambda: fixture_child'),encoding='utf-8')
cmd=[sys.executable,'-B',str(fixed),str(R6/'scripts'),str(WORK/'propagate-invocation-v2'),str(WORK/'failing_upstream_fixture.py')]
p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60,env=env)
receipt=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'PROPAGATE_CHILD_FAILURE_CONFIRMED.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
assert p.returncode==0 and 'rc=7' in p.stdout and 'RETURNED_NORMALLY' in p.stdout, receipt
print(json.dumps(receipt))
modules=['test_codex_c01_review_binding','test_codex_c02a_dependency_verification','test_codex_c02b1_staged_source','test_codex_c02b2_per_actor_reuse','test_gemini_c02b3_asset_reuse','test_gemini_a3_event_tracking','test_gemini_a4_evidence_conformance']
cmd=[sys.executable,'-B','-m','unittest','-v']+modules
t=time.monotonic(); at=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(cmd,cwd=R6/'tests',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,env=env)
receipt=dict(command=cmd,cwd=str(R6/'tests'),started_utc=at,duration_seconds=round(time.monotonic()-t,3),exit_code=p.returncode,
    fixture_root=str(WORK),stdout=p.stdout,stderr=p.stderr)
(OUT/'ROOT_76_TESTS.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(OUT/'ROOT_76_TESTS.log').write_text(p.stderr+'\n--- captured stdout ---\n'+p.stdout,encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('stdout','stderr')}))
print(p.stderr[-3500:])
ident=json.loads((OUT/'CANDIDATE_IDENTITY.json').read_text(encoding='utf-8'))
checks=[]
for row in ident['files']:
    sh=hashlib.sha256(Path(row['snapshot']).read_bytes()).hexdigest()
    checks.append(dict(path=row['snapshot'],expected=row['expected_sha256'],actual=sh,match=sh==row['expected_sha256']))
(OUT/'POST_TEST_HASH_CHECK.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
assert all(x['match'] for x in checks)
for file in ('g1_root_probes.py','g1_run_suite.py','g1_prepare_review.py'):
    shutil.copyfile(BASE/'work'/file,OUT/file)
