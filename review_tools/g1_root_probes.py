from pathlib import Path
import os, sys, json, subprocess, datetime, hashlib, importlib, copy, tempfile
from unittest.mock import patch

BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-20261018'
R6=OUT/'candidate/task/corrections/identity/r6'
WORK=BASE/'work/g1-review-fixtures'
WORK.mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',CUDA_VISIBLE_DEVICES='-1')
for v in ('C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR'):
    os.environ[v]=str(WORK)
sys.path.insert(0,str(R6/'tests'))
results=[]
def record(name,expected,actual):
    r=dict(probe=name,expected=expected,actual=actual)
    results.append(r); print(json.dumps(r,ensure_ascii=True))
def cmd(name,args):
    t=datetime.datetime.now(datetime.timezone.utc)
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60,env=os.environ.copy())
    rec=dict(command=args,started_utc=t.isoformat(),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
    (OUT/(name+'.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return p

# Run the candidate CLI with --help: no GPU, model or video operation is reached.
p=cmd('COTRACKER_CLI',[sys.executable,'-B',str(R6/'scripts/r6_cotracker.py'),'--help'])
record('cotracker_cli_help','exit 0, usage',dict(exit=p.returncode,stderr=p.stderr.strip().splitlines()[-1]))

a4=importlib.import_module('test_gemini_a4_evidence_conformance')
f=a4.EvidenceGateConformanceTests(); f.setUp()
try:
    ns=f.r6/'continuations/root-probe'
    f.matrix.NS=ns
    for rel in ('evidence/F01_excerpts_strip.png','evidence/F01_excerpts_verified.json','tests/test_r6g_microfixes.py','outputs/R6G_MASTER.mp4'):
        p=ns/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b'')
    rows=f.matrix.compute_rows()
    record('matrix_empty_artifacts','no PASS from empty image/json/test/mp4', {q:rows[q]['verdict'] for q in ('Q01','Q05','Q07','Q08')})
    real_root=f.k.R6
    try:
        fake_root=WORK/'manifest-root/r6'; fake_root.mkdir(parents=True,exist_ok=True)
        (fake_root/'must-be-included.json').write_text('{"fixture":true}',encoding='utf-8')
        f.k.R6=fake_root
        record('manifest_work_parent','includes ordinary file outside R6/work',f.matrix.build_manifest())
    finally: f.k.R6=real_root
    invalid={f'Q{i:02d}':'FAIL' for i in range(1,13)}
    record('unknown_gate_mode','GateBlock', f.gate.gate_batch_conformance({'matrix':invalid},mode='finla'))
    record('final_gate_no_artifacts','GateBlock for missing evidence/artifacts',f.gate.gate_batch_conformance({'matrix':{k:'PASS' for k in invalid}},mode='final'))
finally: f.doCleanups()

a3=importlib.import_module('test_gemini_a3_event_tracking')
f=a3.EventTimingAndTrackingTests(); f.setUp()
try:
    import numpy as np
    record('tracker_empty_tensors','reject empty T/N',f.cotracker.validate_cotracker_tensors(np.zeros((0,0,2),dtype=np.float32),np.zeros((0,0),dtype=bool),0,0))
    record('tracker_nonfinite_visibility','reject nonfinite visibility',f.cotracker.validate_cotracker_tensors(np.zeros((2,3,2),dtype=np.float32),np.full((2,3),np.nan),2,3))
    record('tracker_invalid_visibility_range','reject visibility=9',f.cotracker.validate_cotracker_tensors(np.zeros((2,3,2),dtype=np.float32),np.full((2,3),9),2,3))
    row={'events':[], 'contacts':[{'from':9,'to':29}], 'actors':[{'class_windows':[{'from':1,'to':19,'class':'VISIBLE'},{'from':20,'to':29,'class':'FULLY_OCCLUDED'},{'from':30,'to':49,'class':'VISIBLE'},{'from':50,'to':60,'class':'NOT_PRESENT'}]}]}
    record('entry_exit_occlusion_release_keys','include visibility transitions at 20/50 and contact-end boundary',sorted(f.propagate.event_fids_for('S0021',row)))
finally: f.doCleanups()

asset=importlib.import_module('test_gemini_c02b3_asset_reuse')
f=asset.AssetRestyleVerifiedReuseTests(); f.setUp()
try:
    dep=f.generate(review=False)
    record('asset_valid_control','accept genuine fixture deps',f.cache.verify_deps(dep,f.shot,1))
    missing=copy.deepcopy(dep); missing['consumed'].pop('grey_ref'); f.reseal(missing)
    record('asset_missing_consumed_grey','reject missing consumed R1/R2 ref',f.cache.verify_deps(missing,f.shot,1))
    gp=Path(dep['consumed']['graph']['path']); original=gp.read_bytes()
    graph=json.loads(original); graph['SAMPLER']['inputs']['sampler_name']='heun'
    gp.write_text(json.dumps(graph),encoding='utf-8')
    altered=copy.deepcopy(dep)
    altered['consumed']['graph']['sha256']=hashlib.sha256(gp.read_bytes()).hexdigest()
    if 'size' in altered['consumed']['graph']: altered['consumed']['graph']['size']=gp.stat().st_size
    if 'bytes' in altered['consumed']['graph']: altered['consumed']['graph']['bytes']=gp.stat().st_size
    f.reseal(altered)
    record('asset_graph_sampler_differs_recipe','reject graph heun vs recipe euler',dict(recipe=altered['recipe']['sampler'],graph='heun',verifier=f.cache.verify_deps(altered,f.shot,1)))
finally: f.doCleanups()

# Actual run_one launches a real CPU child that exits 7; main/run_shot remain production code.
# Only preconditions/source extraction are fixture boundaries, no upstream inference is launched.
child=WORK/'failing_upstream_fixture.py'; child.write_text('import sys\nprint("fixture upstream child exiting 7",file=sys.stderr)\nsys.exit(7)\n',encoding='utf-8')
driver=WORK/'propagate_cli_driver.py'
driver.write_text('''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import r6_propagate as p
p.NS=Path(sys.argv[2])
p.K.PLAN={'S0021':{'frames':3,'start_frame':0}}
p.G.gate_shot_before_propagate=lambda sid: None
p.build_key_fids=lambda sid,n: [1,3]
p.stage_shot_assets=lambda *args: None
fixture_child=Path(sys.argv[3])
p.blend_script=lambda: fixture_child
sys.argv=['r6_propagate.py','S0021','--nproc','1']
p.main()
print('ROOT_PROBE_PARENT_RETURNED_NORMALLY')
''',encoding='utf-8')
p=cmd('PROPAGATE_CHILD_FAILURE',[sys.executable,'-B',str(driver),str(R6/'scripts'),str(WORK/'propagate-invocation'),str(child)])
record('propagate_cli_child_failure','parent nonzero exit and durable failure receipt',dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
(OUT/'ROOT_PROBES.json').write_text(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),probes=results),ensure_ascii=False,indent=2),encoding='utf-8')
print('ROOT_PROBES_COMPLETE',len(results))
