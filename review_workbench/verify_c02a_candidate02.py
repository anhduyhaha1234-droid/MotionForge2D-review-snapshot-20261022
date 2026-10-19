from pathlib import Path
import datetime,json,os,subprocess,sys
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
R6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6')
target=OUT/'root-review/C02A_TESTS_CANDIDATE02.json'
assert not target.exists()
env=os.environ.copy();env.update(C01_WORKER_DIR=str(OUT/'root-review'),C02A_WORKER_DIR=str(OUT/'root-review'))
runs=[
('C02A_NESTING_CANDIDATE02.txt',['-m','unittest','-v','test_codex_c02a_dependency_verification.DependencyVerificationTests.test_nested_json_matrix_through_loader_verify_key_and_skip','test_codex_c02a_dependency_verification.DependencyVerificationTests.test_parsed_nested_deps_block_actual_assembly_before_copy']),
('C02A_FULL_CANDIDATE02.txt',['-m','unittest','discover','-s',str(R6/'tests'),'-p','test_codex_c0*.py','-v'])]
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':[]}
for name,args in runs:
    cmd=[sys.executable,'-B','-X','utf8',*args];p=OUT/'root-review'/name;assert not p.exists()
    r=subprocess.run(cmd,cwd=R6/'tests',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    p.write_bytes(r.stdout);text=r.stdout.decode('utf-8','replace')
    summary=[line for line in text.splitlines() if line.startswith(('Ran ','OK','FAILED'))]
    rec['runs'].append({'command':cmd,'cwd':str(R6/'tests'),'exit_code':r.returncode,'raw':str(p),'summary':summary})
    print(json.dumps(rec['runs'][-1]))
    if r.returncode:break
target.write_text(json.dumps(rec,indent=2),encoding='utf-8')
sys.exit(0 if len(rec['runs'])==2 and all(x['exit_code']==0 for x in rec['runs']) else 1)

