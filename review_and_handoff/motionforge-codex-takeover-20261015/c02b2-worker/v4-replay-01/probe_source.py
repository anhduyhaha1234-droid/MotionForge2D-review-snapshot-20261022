"""Actual per-actor producer replay; external GPU/adapter/upload boundaries isolated."""
from pathlib import Path
import argparse,hashlib,importlib,json,sys,types
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--scripts',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);(out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
task=out/'task';r6=task/'corrections/identity/r6';sd=r6/'scripts';sd.mkdir(parents=True)
hashes={}
for p in Path(a.scripts).glob('*.py'):
    b=p.read_bytes();(sd/p.name).write_bytes(b);hashes[p.name]=hashlib.sha256(b).hexdigest()
(task/'chunk_plan.json').write_text(json.dumps({'chunks':[{'unit_id':'S0021','start_frame':0,'frames':3}]}))
sys.dont_write_bytecode=True;sys.path.insert(0,str(sd))
K=importlib.import_module('r6_common');C=importlib.import_module('r6_cache')
K.SRC.parent.mkdir(parents=True);K.SRC.write_bytes(b'tiny-source')
C.MODEL_PATH=out/'model.bin';C.MODEL_PATH.write_bytes(b'tiny-model')
row={'shot':'S0021','zero_explicit':False,'n':3,'src':[0,3],'actors':[{'entity':'E1','class_windows':[{'from':1,'to':3,'class':'VISIBLE'}]}],'events':[],'contacts':[]}
(r6/'source_actor_ledger.jsonl').write_text(json.dumps(row)+'\n')
(r6/'storyboard/S0021.json').write_text(json.dumps({'shot':'S0021','n':3,'zero_explicit':False,'keys':[{'fid':1}]}))
for suffix in ('front_bust','profile'):
    p=K.R4/'assets/cast_b'/('B01_Khang_'+suffix+'.png');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(('cast-'+suffix).encode())
mask=r6/'masks/S0021/E1/f_0001.png';mask.parent.mkdir(parents=True);mask.write_bytes(b'mask-bytes')
tpl=task/'graph/reuse_bundle/shot_anchor_v1.baseline.api.json';tpl.parent.mkdir(parents=True)
g={n:{'class_type':'FixtureNode','inputs':{}} for n in ('KEY_LOAD','R1_LOAD','R2_LOAD','R3_LOAD','PROMPT','NOISE','LATENT','SIGMAS','SAMPLER','GUIDER','UNET','CLIP','VAE','SAVE','R2_POS','R2_NEG')}
g['SIGMAS']['inputs']={'steps':4,'width':8,'height':8}
g['SAMPLER']['inputs']={'sampler_name':'euler'}
g['GUIDER']['inputs']={'cfg':1.0}
g['UNET']['inputs']={'unet_name':'model.bin'}
g['CLIP']['inputs']={'clip_name':'qwen_3_4b.safetensors'}
g['VAE']['inputs']={'vae_name':'flux2-vae.safetensors'}
g['NOISE']['inputs']={'noise_seed':1}
g['LATENT']['inputs']={'width':8,'height':8}
g['R2_POS']['inputs']={n:[n,0] for n in ('KEY_LOAD','R1_LOAD','R2_LOAD')};g['R2_NEG']['inputs']={'from':['R2_POS',0]};tpl.write_text(json.dumps(g))
up=types.ModuleType('r6_upload');up.upload_image=lambda p,folder:folder+'/'+Path(p).name;sys.modules['r6_upload']=up
A=types.ModuleType('r6_adapter');A.__file__=str(sd/'r6_adapter.py')
frame=np.arange(1*8*8*3,dtype=np.float32).reshape(1,8,8,3)/192
A.load_img=lambda p:frame.copy();A.load_mask=lambda p:np.ones((1,8,8),dtype=np.float32)
def save_img(arr,p):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_bytes(b'fixture-image'+arr.tobytes())
A.save_img=save_img
A.crop_for_mask=lambda f,m,context_factor:([None,None,None,None,None,f.copy()],dict(x=0,y=0,w=8,h=8,mask_px=64,target=[8,8]))
A.stitch_back=lambda res,edit:edit
A.bound_check=lambda before,after,mask:{'ok':True}
sys.modules['r6_adapter']=A
def stage(sid,gframe,dst):
    dst=Path(dst);dst.write_bytes(b'fixture-staged')
    rec={'contract':K._STAGE_CONTRACT,'source_path':str(K.SRC.resolve()),'source_sha256':K.sha(K.SRC),'sid':sid,'gframe':gframe,'output_path':str(dst.resolve()),'output_sha256':K.sha(dst),'output_size':dst.stat().st_size}
    dst.with_name(dst.name+'.stage.json').write_text(json.dumps(rec))
    return dst
K.stage_frame=stage;calls=[]
edited=K.D/'output/edited.png';edited.parent.mkdir(parents=True);edited.write_bytes(b'fixture-edited')
K.post=lambda graph:calls.append(graph) or {'prompt_id':'fixture'}
K.wait=lambda *args,**kwargs:{}
K.collect_outputs=lambda hist:[edited]
P=importlib.import_module('r6_keygen');G=importlib.import_module('r6_gate')
P.run_key('S0021',1)
key=r6/'keys/S0021/f_0001_key.png'
G.write_review('keys','S0021_f0001',key,G.key_inputs_now('S0021',1,key),{'shot':'S0021','fid':1},'PASS','isolated fixture only',frames=[1],reviewer='fixture-reviewer')
first=len(calls);Cwhy=C.skip_allowed('S0021',1,key)
P.run_key('S0021',1);second=len(calls)
rec={'source_hashes':hashes,'initial_generation_calls':first,'unchanged_replay_generation_calls':second-first,'skip_before_replay':Cwhy,'pass':first==1 and second==first,'scope':'real producer/cache/graph/gate; adapter, staging, upload and GPU boundary substituted; not semantic media proof'}
(out/'RESULT.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec));sys.exit(0 if rec['pass'] else 1)
