from pathlib import Path
import os,sys,json,importlib,types,numpy as np,torch
from unittest.mock import patch
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2');O=BASE/'outputs/motionforge-g1-review-03-20261019';R=O/'candidate/task/corrections/identity/r6';W=BASE/'work/g1-review-03-event-controls';W.mkdir(exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='-1',PYTHONDONTWRITEBYTECODE='1')
for v in ['C01_WORKER_DIR','C02A_WORKER_DIR','C02B1_WORKER_DIR','C02B2_WORKER_DIR','C02B3_WORKER_DIR']:os.environ[v]=str(W)
sys.path.insert(0,str(R/'tests'));a3=importlib.import_module('test_gemini_a3_event_tracking');f=a3.EventTimingAndTrackingTests();f.setUp()
result={}
try:
    led=importlib.import_module('r6_ledger');kg=importlib.import_module('r6_keygen');f.k.SHOTS=['S0021'];f.k.PLAN={'S0021':{'start_frame':0,'frames':60}}
    led.R3_LEDGER=f.root/'source_ledger.json';led.R5_SB=f.root/'old_storyboard';led.R5_SB.mkdir()
    led.R3_LEDGER.write_text(json.dumps({'shots':{'S0021':{'src':[0,60],'actors':[{'entity':'E1'}],'events':[{'frame':43}],'contacts':[{'from':9,'to':29}]}}}))
    (led.R5_SB/'S0021.json').write_text(json.dumps({'keys':[{'fid':1},{'fid':60}]}))
    led.OVR={'S0021':{'actors':{'E1':[(1,19,'VISIBLE'),(20,29,'FULLY_OCCLUDED'),(30,49,'VISIBLE'),(50,60,'NOT_PRESENT')]}}};led.main()
    calls=[]
    with patch.object(kg,'run_key',side_effect=lambda sid,fid:calls.append(fid)),patch.object(sys,'argv',['r6_keygen.py','S0021']):kg.main()
    with patch.object(f.propagate.G,'gate_key',return_value=True):gate=f.propagate.G.gate_shot_before_propagate('S0021')
    result['actual_event_call_path']={'board_fids':[x['fid'] for x in json.loads((f.k.R6/'storyboard/S0021.json').read_text())['keys']],'keygen_fids':calls,'gate':gate,'propagate_fids':f.propagate.build_key_fids('S0021',60),'stub_boundaries':'generation and per-key semantic reviews only; actual ledger/main/discovery/gate requirement/propagation preserved'}
    c=f.cotracker;c.ckpt=lambda:W/'unused-weights';c.load_frames=lambda sid,kind:np.zeros((50,360,640,3),dtype=np.uint8)
    results=[]
    for mode in ['no_visible','good','offset']:
        class Predictor:
            def __init__(self,**kw):self.calls=0
            def to(self,dev):return self
            def __call__(self,video,queries):
                self.calls+=1;tr=torch.zeros((1,video.shape[1],queries.shape[1],2));vis=torch.ones((1,video.shape[1],queries.shape[1]),dtype=torch.bool)
                if mode=='no_visible':vis[:]=False
                if mode=='offset' and self.calls==2:tr[:,:,:,0]=10
                return tr,vis
        mod=types.ModuleType('cotracker.predictor');mod.CoTrackerPredictor=Predictor
        (f.k.R6/'event_map.json').write_text(json.dumps({'shots':{'S0034':{'events':[{'frame':43}],'contacts':[]}}}))
        c.OUTD=W/mode;c.OUTD.mkdir();c.REC=c.OUTD/'receipt.jsonl'
        with patch.dict(sys.modules,{'cotracker.predictor':mod}),patch.object(sys,'argv',['r6_cotracker.py','S0034']):c.main()
        raw=c.REC.read_text();rec=json.loads(raw.splitlines()[-1]);results.append({'mode':mode,'fid':rec['windows'][0]['fid'],'drift':rec['windows'][0]['drift_contact_mean'],'no_NaN':'NaN' not in raw,'scope':'actual CLI/run/window code; controlled predictor tensors and load_frames, no weights/GPU/media-quality claim'})
    result['actual_tracker_window_controls']=results
finally:f.doCleanups()
(O/'EVENT_CONTROLS.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
