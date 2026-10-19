from pathlib import Path
import ast, hashlib, json, os, sys, time, types
from PIL import Image, ImageDraw, ImageFont
import subprocess
ROOT=Path(r'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
O=ROOT/'outputs/motionforge-r6-checkpoint-review-20261014'
RUN=Path(r'C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
D=RUN/'tasks/MF-DEMO-LONG-01';R6=D/'corrections/identity5m_20261008/r6'
SNAP=O/'snapshot/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6'
P=O/'fresh_probes';P.mkdir(exist_ok=True)
results={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_functions(p, env):
    tree=ast.parse(p.read_text(encoding='utf-8'))
    # Execute exact function/class bodies only: no module-level mkdir/import side effects.
    tree.body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    exec(compile(tree,str(p),'exec'),env)
    return env
def save(name,x):
    p=O/name;assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def probes():
    # Run unmodified gate function bodies against reviewer-owned synthetic inputs.
    import hashlib as hh
    K=types.SimpleNamespace(R6=P,sha=sha)
    env={'Path':Path,'K':K,'REV':P/'reviews','hashlib':hh,'json':json,'time':time}
    g=load_functions(SNAP/'scripts/r6_gate.py',env)
    key=P/'white.png';Image.new('RGB',(640,360),'white').save(key)
    g['write_review']('keys','minimal',key,{}, {},'PASS','unverified synthetic empty review','')
    try:g['require_review']('keys','minimal',key,{'ledger_row_sha':'changed','deps_sha':'changed'}); got='ACCEPTED'
    except g['GateBlock'] as e:got=str(e)
    results['empty_binding_review']={'expected':'BLOCK required input/semantic fields absent','actual':got,'meaning':'Integrity bypass only; not a claim a machine can judge arbitrary image semantics.'}
    g['write_review']('keys','control',key,{'deps_sha':'good'},{},'PASS','synthetic integrity control')
    try:g['require_review']('keys','control',key,{'deps_sha':'bad'}); got='ACCEPTED'
    except g['GateBlock'] as e:got=str(e)
    results['stale_nonempty_binding_control']={'expected':'BLOCK','actual':got}
    bd=P/'work/S0099/blend';bd.mkdir(parents=True)
    for i in range(1,11):
        p=bd/f'{i:04d}.jpg';Image.new('RGB',(8,8),(i,0,0)).save(p);os.utime(p,(1000,1000))
    start=time.time()-1;os.utime(bd/'0010.jpg',None)
    try:got=g['gate_blend_fresh']('S0099',10,start)
    except g['GateBlock'] as e:got=str(e)
    results['nine_stale_one_fresh']={'expected':'BLOCK nine stale outputs','actual':got}
    # Execute actual propagation wrapper with approved-gate stub and failed-inner/rc0 runner.
    # No upstream/Hermes/Comfy subprocess can run: K.run is a local stub.
    sid='S0098';b=P/'work'/sid;b.mkdir(parents=True)
    for sub in ['blend','video']:(b/sub).mkdir()
    for i in range(1,12):
        Image.new('RGB',(8,8),'black').save(b/'video'/f'{i:04d}.png')
    for i in range(1,11):
        p=b/'blend'/f'{i:04d}.jpg';Image.new('RGB',(8,8),'white').save(p);os.utime(p,(1000,1000))
    kd=P/'keys'/sid;kd.mkdir(parents=True)
    for i in [1,11]:Image.new('RGB',(640,368),'white').save(kd/f'f_{i:04d}_key.png')
    (P/'receipts').mkdir(exist_ok=True)
    K.PLAN={sid:{'frames':11,'start_frame':0}};K.R4=P/'vendor_stub';K.TMPD=P/'tmp';K.ENVPY='NEVER_LAUNCHED'
    def fake_runner(*args,**kwargs):
        time.sleep(0.05)
        now=time.time();os.utime(b/'blend/0010.jpg',(now,now))
        return 0,types.SimpleNamespace(returncode=0,stderr='inner child failed; older output files remain',stdout='')
    K.run=fake_runner
    import shutil
    pe={'K':K,'G':types.SimpleNamespace(gate_shot_before_propagate=lambda sid:True),'Path':Path,'json':json,'os':os,'shutil':shutil,'sys':sys,'time':time,'REC':P/'receipts/propagation.jsonl'}
    pg=load_functions(SNAP/'scripts/r6_propagate.py',pe);pg['blend_script']=lambda:P/'stub_video_blend.py'
    try:got=pg['run_shot'](sid)
    except BaseException as e:got=type(e).__name__+': '+str(e)
    results['actual_propagation_partial_refresh']={'expected':'BLOCK stale prior outputs despite outer rc0','actual':got,'runner':'synthetic failure injection; approved input-gate stub; no inference'}
    ev=json.loads((SNAP/'event_map.json').read_text(encoding='utf-8'))
    for sid in ['S0034','S0061','S0073']:
        # Exact r6_cotracker selection logic, schema shape verified from bytes.
        events=[e for e in ev.get(sid,[])] if isinstance(ev.get(sid),list) else ev.get(sid,{}).get('events',[])
        results[f'event_reader_{sid}']={'actual_selected':events,'actual_source_events':ev.get('shots',{}).get(sid)}
    off=[]
    for line in (R6/'source_actor_ledger.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line);sbp=R6/'storyboard'/f"{r['shot']}.json"
        if not sbp.exists():continue
        sb=json.loads(sbp.read_text(encoding='utf-8'));fids=[k['fid'] for k in sb['keys']]
        dropped=[f for f in fids if (f-1)%10]
        if dropped:off.append({'shot':r['shot'],'off_grid_fids':dropped})
    results['keys_omitted_by_grid_staging']=off
    save('FRESH_PROBES.json',results)
def visuals():
    plan=json.loads((D/'chunk_plan.json').read_text(encoding='utf-8'))['chunks']
    shots=[c for c in plan if 21<=int(c['unit_id'][1:])<=74]
    samples=[]
    for c in shots:
        g=max(2820,c['start_frame'])+min(c['frames'],11820-c['start_frame'])//2
        samples.append({'shot':c['unit_id'],'global_frame':g,'pilot_frame':g-2820,'tag':'mid'})
    detail={22:[0,30,60],33:[0,30,60],61:[100,110,170],62:[32,60,111],70:[0,30,60],73:[0,40,90,140,178],74:[0,60,100]}
    for sid,fids in detail.items():
        c=next(c for c in shots if int(c['unit_id'][1:])==sid)
        for f in fids:
            g=c['start_frame']+f
            if g<11820 and f<c['frames']:samples.append({'shot':c['unit_id'],'global_frame':g,'pilot_frame':g-2820,'tag':f'f0={f}'})
    V=O/'visual';V.mkdir(exist_ok=True)
    sources={'source':(D/'source/source_full.mp4','global_frame'),'R5':(R6.parent/'r5/outputs/IDENTITY5M_R5_MASTER.mp4','pilot_frame'),'R6':(R6/'outputs/IDENTITY5M_R6_MASTER.mp4','pilot_frame')}
    images={}
    for kind,(path,field) in sources.items():
        frames=sorted(set(s[field] for s in samples));dest=V/kind;dest.mkdir()
        filt='select='+ '+'.join(f'eq(n\\,{f})' for f in frames)
        cmd=['ffmpeg','-v','error','-i',str(path),'-vf',filt,'-vsync','0',str(dest/'%04d.png')]
        rr=subprocess.run(cmd,capture_output=True,text=True);assert rr.returncode==0,rr.stderr
        got=sorted(dest.glob('*.png'));assert len(got)==len(frames),(kind,len(got),len(frames))
        images[kind]={f:p for f,p in zip(frames,got)}
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    sheetpaths=[]
    for k in range(0,len(samples),9):
        chunk=samples[k:k+9];sheet=Image.new('RGB',(972,213*len(chunk)),(20,20,20));dr=ImageDraw.Draw(sheet)
        for row,s in enumerate(chunk):
            for col,(kind,(_,field)) in enumerate(sources.items()):
                x=col*324;y=row*213
                dr.text((x+4,y+3),f"{s['shot']} {s['tag']} {kind} t={s['pilot_frame']/30:.3f}",font=font,fill='white')
                im=Image.open(images[kind][s[field]]);sheet.paste(im.resize((320,180)),(x+2,y+25))
        p=V/f'contact_{k//9+1:02d}.jpg';sheet.save(p,quality=94);sheetpaths.append(str(p))
    save('VISUAL_INDEX.json',{'scope':'Fresh exact decoded frames: 54 midpoints + targeted frames, no continuous playback','samples':samples,'sheets':sheetpaths})
if __name__=='__main__':
    probes();visuals();print(json.dumps(results,ensure_ascii=True,indent=2))
