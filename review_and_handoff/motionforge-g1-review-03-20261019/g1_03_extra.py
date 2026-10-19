from pathlib import Path
import os,sys,importlib.util,importlib,json,hashlib,datetime,subprocess,shutil,unittest,io,contextlib,copy
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2');O=BASE/'outputs/motionforge-g1-review-03-20261019'
R=O/'candidate/task/corrections/identity/r6';W=BASE/'work/g1-review-03-extra';W.mkdir(exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='-1')
for k in ['C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR']:os.environ[k]=str(W)
sys.path.insert(0,str(R/'tests'))
def obs(fn):
    try:return {'returned':fn()}
    except BaseException as e:return {'exception':type(e).__name__,'detail':str(e)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    return {'command':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
spec=importlib.util.spec_from_file_location('r6_event_contract',R/'scripts/r6_event_contract.py');ec=importlib.util.module_from_spec(spec);spec.loader.exec_module(ec)
data['strict_events']=[{'input':v,'result':obs(lambda v=v:ec.parse_event_fid(v,50,'S0034'))} for v in [{'frame':43.9},{'frame':True},{'frame':'43'},{'f':42.8,'frame':43.2}]]
from pydantic import TypeAdapter,StrictInt
adapter=TypeAdapter(StrictInt)
data['installed_strictint_comparison']=[{'input':v,'result':obs(lambda v=v:adapter.validate_python(v))} for v in [43.9,True,'43',43]]
asset=importlib.import_module('test_gemini_c02b3_asset_reuse')
buf=io.StringIO()
with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
    suite=unittest.defaultTestLoader.loadTestsFromModule(asset)
    rr=unittest.TextTestRunner(stream=buf,verbosity=2).run(suite)
data['focused_asset_suite']={'run':rr.testsRun,'failures':len(rr.failures),'errors':len(rr.errors),'raw':buf.getvalue(),'scope':'Only asset module10, not broad89. Exact snapshot; external inference/storage stubbed by fixture.'}
f=asset.AssetRestyleVerifiedReuseTests();f.setUp()
try:
    dep=f.generate(review=True);gp=Path(dep['consumed']['graph']['path']);orig=gp.read_bytes()
    baseline=f.cache.skip_allowed(f.shot,1,f.key());cases=[]
    for tag in ['wrong_grey','missing_R1']:
        g=json.loads(orig)
        if tag=='wrong_grey':g['R1_LOAD']['inputs']['image']='wrong_invocation/fake_grey.png'
        else:g.pop('R1_LOAD')
        gp.write_text(json.dumps(g),encoding='utf-8');d=copy.deepcopy(dep);d['consumed']['graph']['sha256']=sha(gp);f.reseal(d);f.write_dep(d)
        # Rebind fixture review to corrupted bytes; verifier must still reject actual graph.
        f.gate.write_review('keys',f'{f.shot}_f0001',f.key(),f.gate.key_inputs_now(f.shot,1,f.key()),{'identity':'PASS','pose':'PASS','style':'PASS'},'PASS','root probe') if False else None
        cases.append({'tag':tag,'skip_allowed':f.cache.skip_allowed(f.shot,1,f.key()),'deps_verify':f.cache.verify_deps(d,f.shot,1)})
    data['actual_producer_reuse_mutations']={'valid':baseline,'cases':cases}
finally:f.doCleanups()
vend=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r4/vendor/Rerender_A_Video-dfaf9d8825f226a2f0a0b731ab2adc84a3f2ebd2')
seq_path=vend/'blender/video_sequence.py';spec=importlib.util.spec_from_file_location('root_upstream_sequence',seq_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
seq=m.VideoSequence(str(W/'upstream_sequence'),11,21,10)
data['upstream_names']={'file':str(seq_path),'sha256':sha(seq_path),'beg':11,'end':21,'actual_names':[Path(seq.get_blending_img(i)).name for i in range(seq.get_sequence_beg_id(0),seq.get_sequence_beg_id(1))],'candidate_required':[f'{i:04d}.jpg' for i in range(1,11)],'scope':'Pure upstream naming API only; no flow/model/GPU invoked'}
bad=BASE/'work/g1-03-audit/sandbox/r6/continuations/test-matrix/outputs/R6G_MASTER.mp4'
data['ffprobe_same_fake_video']=run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(bad)])
out=W/'valid_3_frames.mp4'
data['cpu_fixture_generation']=run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=30','-frames:v','3','-c:v','mpeg4',str(out)])
data['ffprobe_valid_control']=run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)])
(O/'EXTRA_PROBES.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
audit=O/'delegated_audit';audit.mkdir(exist_ok=True)
for n in ['PROBE_RESULTS.json','probe_submission.py']:
    dst=audit/n;assert not dst.exists();shutil.copyfile(BASE/'work/g1-03-audit'/n,dst)
for n in ['g1_03_prepare.py','g1_03_probes.py','g1_03_extra.py']:
    dst=O/n;assert not dst.exists();shutil.copyfile(BASE/'work'/n,dst)
print(json.dumps({'focused':{'run':rr.testsRun,'failures':len(rr.failures),'errors':len(rr.errors)},'strict_events':data['strict_events'],'upstream_names':data['upstream_names'],'fake_video_ffprobe_exit':data['ffprobe_same_fake_video']['exit'],'valid_video_ffprobe_exit':data['ffprobe_valid_control']['exit']}))
