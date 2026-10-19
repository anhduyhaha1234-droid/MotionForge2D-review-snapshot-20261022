from pathlib import Path
import os,sys,subprocess,json,datetime
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2');O=BASE/'outputs/motionforge-g1-review-03-20261019';W=BASE/'work/g1-review-03-boundaries';W.mkdir(exist_ok=True)
R=O/'candidate/task/corrections/identity/r6'
child=W/'global_frame_child.py'
child.write_text('''import sys
from pathlib import Path
from PIL import Image
base=Path(sys.argv[1]);beg=int(sys.argv[sys.argv.index('--beg')+1]);end=int(sys.argv[sys.argv.index('--end')+1])
for fid in range(beg,end):
    im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(base/'blend'/f'{fid:04d}.jpg')
''',encoding='utf-8')
driver=W/'driver.py'
driver.write_text('''from pathlib import Path
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
''',encoding='utf-8')
rows=[]
for mode in ['preflight_fail','stage_systemexit','global_names_import_injected']:
    root=W/mode;root.mkdir();args=[sys.executable,'-B',str(driver),str(R/'scripts'),str(root),str(child),mode]
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    man=root/'r6/work/S0021/blend_manifest.json';rec=root/'receipts.jsonl'
    rows.append({'case':mode,'command':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'stale_manifest':man.exists() and man.read_text()=='STALE_SENTINEL','failure_receipt':rec.exists(),'scope':'CPU children/staging fixture; original candidate except explicitly labeled Image injection diagnostic.'})
(O/'PROPAGATION_BOUNDARIES.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':rows},indent=2),encoding='utf-8')
print(json.dumps(rows))
