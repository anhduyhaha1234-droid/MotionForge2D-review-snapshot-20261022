from pathlib import Path
import sys,json
from PIL import Image
sys.path.insert(0,sys.argv[1]);import r6_propagate as p
root=Path(sys.argv[2]);child=Path(sys.argv[3]);mode=sys.argv[4];p.NS=root/'ns';p.REC=root/'receipts.jsonl'
p.K.R6=root/'r6';p.K.PLAN={'S0021':{'frames':21,'start_frame':0}}
man=p.K.R6/'work/S0021/blend_manifest.json';man.parent.mkdir(parents=True);man.write_text('STALE_SENTINEL')
kd=p.K.R6/'keys/S0021';kd.mkdir(parents=True)
im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(kd/'f_0021_key.png')
p.G.gate_shot_before_propagate=lambda sid:None
p.G.ledger_row=lambda sid:{'cuts':[11]}
p.build_key_fids=lambda sid,n:[1,11,21]
p.stage_shot_assets=lambda *a:None;p.blend_script=lambda:child
if mode=='preflight_fail':
    def bad_gate(sid):raise p.G.GateBlock('root injected invalid input')
    p.G.gate_shot_before_propagate=bad_gate
elif mode=='stage_systemexit':
    def bad_stage(*a):raise SystemExit('EVENT_KEY_MISSING controlled fixture')
    p.stage_shot_assets=bad_stage
elif mode=='global_names_import_injected':
    p.Image=Image # diagnostic only: unblock missing import to isolate upstream naming bug
sys.argv=['r6_propagate.py','S0021','--nproc','1'];p.main()
