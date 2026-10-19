"""C01 adversarial probe: compare reviewed frame identity to actual bound blend."""
from pathlib import Path
import argparse, hashlib, importlib, json, sys
ap=argparse.ArgumentParser(); ap.add_argument('--scripts',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
src=Path(args.scripts); out=Path(args.out).resolve(); assert not out.exists(); out.mkdir(parents=True)
(out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
task=out/'task'; r6=task/'corrections/identity/r6'; sd=r6/'scripts'; sd.mkdir(parents=True)
hashes={}
for name in ['r6_common.py','r6_gate.py']:
    b=(src/name).read_bytes(); (sd/name).write_bytes(b); hashes[name]=hashlib.sha256(b).hexdigest()
sid='S0021'
(task/'chunk_plan.json').write_text(json.dumps({'chunks':[{'unit_id':sid,'start_frame':2820,'frames':3}]}))
sys.dont_write_bytecode=True; sys.path.insert(0,str(sd)); K=importlib.import_module('r6_common'); G=importlib.import_module('r6_gate')
(r6/'source_actor_ledger.jsonl').write_text(json.dumps({'shot':sid,'n':3,'actors':[],'contacts':[],'events':[]})+'\n')
(r6/'storyboard'/f'{sid}.json').write_text(json.dumps({'keys':[{'fid':1}]}))
wd=r6/'work'/sid; bd=wd/'blend'; bd.mkdir(parents=True)
kd=r6/'keys'/sid; kd.mkdir(); key=kd/'f_0001_key.png'; key.write_bytes(b'fixture key bytes')
(wd/'f_0001.deps.json').write_text('{"fixture":"bound"}')
G.write_review('keys',sid+'_f0001',key,G.key_inputs_now(sid,1,key),{'shot':sid,'fid':1},'PASS','fixture only',frames=[1])
frames=[]
for n in range(1,4):
    f=bd/f'{n:04}.jpg'; f.write_bytes(f'fixture frame {n}'.encode()); frames.append({'name':f.name,'sha256':K.sha(f),'size':f.stat().st_size})
man=wd/'blend_manifest.json'; man.write_text(json.dumps({'frames':frames,'blend_dir':str(bd),'child_outcomes':[{'rc':0}],'decode_ok':True,'key_set_sha':'a'*64,'child_outcomes_sha':'b'*64}))
results=[]
for label, reviewed, count, expected in [('full',[1,2,3],3,'ACCEPT'),('truncated_self_consistent',[1],1,'BLOCK'),('overlong_self_consistent',[1,2,3,4],4,'BLOCK')]:
    G.write_review('blend',sid+'_blend',man,G.blend_inputs_now(sid),{'shot':sid,'frames':count},'PASS','fixture only',frames=reviewed)
    try: G.gate_assemble([(sid,3)]); actual='ACCEPT'; detail=''
    except G.GateBlock as e: actual='BLOCK'; detail=str(e)
    except Exception as e: actual='UNCONTROLLED_EXCEPTION'; detail=repr(e)
    results.append({'case':label,'expected':expected,'actual':actual,'pass':actual==expected,'detail':detail})
rec={'source_hashes':hashes,'cases':results,'scope':'Real gate_assemble against isolated fixtures; semantic/decode correctness not asserted.'}
(out/'RESULT.json').write_text(json.dumps(rec,indent=2)); print(json.dumps(rec))
raise SystemExit(0 if all(x['pass'] for x in results) else 1)
