from pathlib import Path
import os, sys, json, subprocess, datetime, hashlib, importlib, copy, time, types, shutil
from unittest.mock import patch
import numpy as np

BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-02-20261018'
R6=OUT/'candidate/task/corrections/identity/r6'
WORK=BASE/'work/g1-review-02-fixtures'
WORK.mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',CUDA_VISIBLE_DEVICES='-1')
for v in ('C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR'):
    os.environ[v]=str(WORK)
sys.path.insert(0,str(R6/'tests'))
results=[]
def record(name,expected,actual):
    r=dict(probe=name,expected=expected,actual=actual)
    results.append(r); print(json.dumps(r,ensure_ascii=True))
def observe(fn):
    try:return dict(returned=fn())
    except BaseException as e:return dict(exception=type(e).__name__,detail=str(e))
def command(name,args,cwd=None):
    t=time.monotonic(); at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60,env=os.environ.copy(),cwd=cwd)
    rec=dict(command=args,cwd=str(cwd),started_utc=at,duration_seconds=round(time.monotonic()-t,3),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
    (OUT/(name+'.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return rec
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data if isinstance(data,bytes) else json.dumps(data).encode())

p=command('COTRACKER_CLI',[sys.executable,'-B',str(R6/'scripts/r6_cotracker.py'),'--help'])
record('cli_help','exit0 usage',dict(exit=p['exit_code'],usage='usage:' in p['stdout']))

asset=importlib.import_module('test_gemini_c02b3_asset_reuse')
f=asset.AssetRestyleVerifiedReuseTests();f.setUp()
try:
    dep=f.generate(review=False)
    record('asset_valid_control','accept genuine actual-producer deps',f.cache.verify_deps(dep,f.shot,1))
    for variant in ('missing','null','wrong_role','wrong_path'):
        dd=copy.deepcopy(dep)
        if variant=='missing':dd['consumed'].pop('grey_ref')
        elif variant=='null':dd['consumed']['grey_ref']=None
        elif variant=='wrong_role':dd['consumed']['grey_ref']['role']='other'
        else:dd['consumed']['grey_ref']['path']=dd['consumed']['staged_source']['path']
        f.reseal(dd);record('asset_grey_'+variant,'reject resealed invalid consumed reference',f.cache.verify_deps(dd,f.shot,1))
    gp=Path(dep['consumed']['graph']['path']);original=gp.read_bytes()
    for variant in ('sampler','wrong_grey_path','missing_R1'):
        graph=json.loads(original)
        if variant=='sampler':graph['SAMPLER']['inputs']['sampler_name']='heun'
        elif variant=='wrong_grey_path':graph['R1_LOAD']['inputs']['image']='wrong_invocation/fake_grey.png'
        else:graph.pop('R1_LOAD')
        put(gp,graph);dd=copy.deepcopy(dep);dd['consumed']['graph']['sha256']=hashlib.sha256(gp.read_bytes()).hexdigest();f.reseal(dd)
        record('asset_graph_'+variant,'reject effective graph mutation despite resealed digest',f.cache.verify_deps(dd,f.shot,1))
    gp.write_bytes(original)
finally:f.doCleanups()

a4=importlib.import_module('test_gemini_a4_evidence_conformance')
f=a4.EvidenceGateConformanceTests();f.setUp()
try:
    ns=f.r6/'continuations/root02';f.matrix.NS=ns
    for rel in ('evidence/F01_excerpts_strip.png','evidence/F01_excerpts_verified.json','tests/test_r6g_microfixes.py','outputs/R6G_MASTER.mp4'):
        put(ns/rel,b'')
    rows=f.matrix.compute_rows()
    record('matrix_empty','UNKNOWN',{q:rows[q]['verdict'] for q in ('Q01','Q05','Q07','Q08')})
    put(ns/'evidence/F01_excerpts_strip.png',b'not an image'*100)
    put(ns/'evidence/F01_excerpts_verified.json',{'verdict':'PASS','shots':['WRONG_SHOT'],'invocation':'other','sha256':'0'*64})
    put(ns/'tests/test_r6g_microfixes.py',b'# no executed assertions\n'*10)
    put(f.k.R6/'work/WRONG/f_0001.deps.json',{'kind':'r6_key_deps_v4_asset','padding':'x'*70})
    put(ns/'outputs/R6G_MASTER.mp4',b'not a video'+b'x'*1000000)
    put(ns/'receipts/R6G_ASSEMBLY_RECEIPT.json',{'frames':9000,'master_bytes':(ns/'outputs/R6G_MASTER.mp4').stat().st_size,'invocation':'other','sha256':'0'*64})
    rows=f.matrix.compute_rows()
    record('matrix_fake_evidence','no PASS for invalid media, nonexistent tests, fake deps, stale receipts',{q:rows[q]['verdict'] for q in ('Q01','Q05','Q07','Q08')})
    fake={f'Q{i:02d}':'UNKNOWN' for i in range(1,13)};fake.update(Q05='PASS',Q07='PASS')
    record('engineering_no_proof','GateBlock',observe(lambda:f.gate.gate_batch_conformance({'matrix':fake},'engineering')))
    record('unknown_mode','GateBlock',observe(lambda:f.gate.gate_batch_conformance({'matrix':fake},'finla')))
    record('final_missing_artifacts','GateBlock',observe(lambda:f.gate.gate_batch_conformance({'matrix':{q:'PASS' for q in fake}},'final')))
    root=f.k.R6
    try:
        f.k.R6=WORK/'manifest/work/r6';put(f.k.R6/'must_include.json',{'fixture':True});put(f.k.R6/'work/internal.json',{'skip':True})
        manifest=f.matrix.build_manifest();record('manifest_work_ancestor','includes must_include.json, skips internal work',[x['path'] for x in manifest['items']])
    finally:f.k.R6=root
    # Actual CLI writer publishes matrix and manifest before checking batch conformance.
    f.matrix.NS=f.r6/'continuations/root02-blocked';f.matrix.NS.mkdir(parents=True)
    f.matrix.compute_rows=lambda:{q:{'verdict':'UNKNOWN'} for q in fake}
    result=observe(f.matrix.main)
    record('matrix_gate_before_publish','blocked candidate must not be published as submission',dict(result=result,matrix_written=(f.matrix.NS/'R6_MATRIX_EVIDENCE.json').exists(),manifest_written=(f.matrix.NS/'R6G_MANIFEST.json').exists()))
finally:f.doCleanups()

a3=importlib.import_module('test_gemini_a3_event_tracking')
f=a3.EventTimingAndTrackingTests();f.setUp()
try:
    for name,tr,vis,t,n in [
        ('empty',np.zeros((0,0,2)),np.zeros((0,0)),0,0),
        ('vis_nan',np.zeros((2,3,2)),np.full((2,3),np.nan),2,3),
        ('vis9',np.zeros((2,3,2)),np.full((2,3),9),2,3),
        ('valid',np.zeros((2,3,2)),np.ones((2,3),dtype=bool),2,3)]:
        record('tracker_'+name,'accept only valid',observe(lambda:f.cotracker.validate_cotracker_tensors(tr,vis,t,n)))
    row={'n':60,'events':[{'frame':43}],'contacts':[{'from':9,'to':29}], 'actors':[{'class_windows':[{'from':1,'to':19,'class':'VISIBLE'},{'from':20,'to':29,'class':'FULLY_OCCLUDED'},{'from':30,'to':49,'class':'VISIBLE'},{'from':50,'to':60,'class':'NOT_PRESENT'}]}]}
    record('event_boundaries','include20/50',sorted(f.propagate.event_fids_for('S0021',row)))
    record('event_conflict','reject',observe(lambda:f.propagate.event_fids_for('S0021',{'n':60,'events':[{'f':9,'frame':43}]})))
    record('event_invalid_contact','reject',observe(lambda:sorted(f.propagate.event_fids_for('S0021',{'n':60,'contacts':[{'from':-10,'to':700}]}))))
    # Test actual CoTracker consumer/CLI with controlled predictor; no weights, GPU or real media.
    import torch
    c=f.cotracker; c.ckpt=lambda: WORK/'fake-weights-unused'
    c.load_frames=lambda sid,kind:np.zeros((50,360,640,3),dtype=np.uint8)
    class Predictor:
        def __init__(self,**kwargs):pass
        def to(self,dev):return self
        def __call__(self,video,queries):
            return torch.zeros((1,video.shape[1],queries.shape[1],2)),torch.ones((1,video.shape[1],queries.shape[1]),dtype=torch.bool)
    mod=types.ModuleType('cotracker.predictor');mod.CoTrackerPredictor=Predictor
    for tag,events in [('frame43',[{'frame':43,'event':'entry'}]),('out_of_range',[{'f':700,'event':'entry'}])]:
        put(f.k.R6/'event_map.json',{'shots':{'S0034':{'events':events,'contacts':[]}}})
        c.OUTD=WORK/('tracker_'+tag);c.OUTD.mkdir(parents=True,exist_ok=True);c.REC=c.OUTD/'receipt.jsonl'
        with patch.dict(sys.modules,{'cotracker.predictor':mod}),patch.object(sys,'argv',['r6_cotracker.py','S0034']):
            status=observe(c.main)
        rec=json.loads(c.REC.read_text().splitlines()[-1]) if c.REC.exists() else None
        record('tracker_actual_cli_'+tag,'frame43 preserved; out-of-range event rejected',dict(status=status,windows=rec and rec['windows']))
    p=f.propagate;p.K.PLAN={'S0021':{'frames':41,'start_frame':0,'cuts':[21]}}
    captured={}
    def spy(fids,m,cuts=None):
        captured.update(fids=fids,m=m,cuts=cuts);raise RuntimeError('STOP_AFTER_PLAN')
    with patch.object(p.G,'gate_shot_before_propagate',return_value=None),patch.object(p,'build_key_fids',return_value=[1,11,21,31,41]),patch.object(p,'plan_runs',side_effect=spy):
        observe(lambda:p.run_shot('S0021'))
    record('propagate_actual_cut_caller','cuts argument passed or intra-shot cuts explicitly rejected',captured)
finally:f.doCleanups()

# Real CPU subprocess: child output test. Only staging/preflight boundaries stubbed.
child=WORK/'fixture_blend_child.py'
child.write_text('''from pathlib import Path
import sys,os
from PIL import Image
base=Path(sys.argv[1]);mode=os.environ['ROOT_OUTPUT_CASE']
if mode=='rc7':sys.exit(7)
names={'valid':['0001.jpg','0002.jpg'],'wrong':['9001.jpg','9002.jpg'],'extra':['0000.jpg','0001.jpg','0002.jpg'],'corrupt':['0001.jpg','0002.jpg']}[mode]
for name in names:
    if mode=='corrupt':(base/'blend'/name).write_bytes(b'not-jpeg');continue
    im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(base/'blend'/name)
''',encoding='utf-8')
driver=WORK/'propagate_driver.py'
driver.write_text('''from pathlib import Path
import sys,json
from PIL import Image
sys.path.insert(0,sys.argv[1]);import r6_propagate as p
root=Path(sys.argv[2]);child=Path(sys.argv[3]);p.NS=root/'ns';p.REC=root/'receipts.jsonl'
p.K.R6=root/'r6';p.K.PLAN={'S0021':{'frames':3,'start_frame':0}}
man=p.K.R6/'work/S0021/blend_manifest.json';man.parent.mkdir(parents=True);man.write_text('STALE_SENTINEL')
kd=p.K.R6/'keys/S0021';kd.mkdir(parents=True)
im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(kd/'f_0003_key.png')
p.G.gate_shot_before_propagate=lambda sid:None
p.build_key_fids=lambda sid,n:[1,3];p.stage_shot_assets=lambda *a:None;p.blend_script=lambda:child
sys.argv=['r6_propagate.py','S0021','--nproc','1'];p.main()
''',encoding='utf-8')
for case in ('rc7','valid','wrong','extra','corrupt'):
    target=WORK/('propagate_'+case);target.mkdir()
    os.environ['ROOT_OUTPUT_CASE']=case
    rec=command('PROPAGATE_'+case,[sys.executable,'-B',str(driver),str(R6/'scripts'),str(target),str(child)])
    man=target/'r6/work/S0021/blend_manifest.json';receipt=target/'receipts.jsonl'
    record('propagate_real_child_'+case,'valid rc0; all invalid nonzero with invalidated stale manifest',dict(exit=rec['exit_code'],stdout=rec['stdout'],stderr=rec['stderr'],manifest_exists=man.exists(),manifest_stale=(man.read_text()=='STALE_SENTINEL') if man.exists() else False,receipt_exists=receipt.exists()))

(OUT/'ROOT_PROBES.json').write_text(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),probes=results),ensure_ascii=False,indent=2),encoding='utf-8')
print('ROOT_PROBES_COMPLETE',len(results))
