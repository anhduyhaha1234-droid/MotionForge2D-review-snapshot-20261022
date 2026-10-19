from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, types
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
out=Path(a.out).resolve();out.mkdir(exist_ok=False,parents=True)
(out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
task=out/'task';scripts=task/'corrections/identity/r6/scripts';scripts.mkdir(parents=True)
p=scripts/'r6_common.py';p.write_bytes(Path(a.source).read_bytes())
(task/'chunk_plan.json').write_text(json.dumps({'chunks':[{'unit_id':'S0021','start_frame':0,'frames':10}]}))
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('root_staging_common',p);k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
k.SRC.parent.mkdir(parents=True);k.SRC.write_bytes(b'SOURCE-A')
src2=k.SRC.parent/'other.mp4';src2.write_bytes(b'SOURCE-A')
dst=out/'frame.png';calls=[];cases=[]
def fake_run(cmd,**kwargs):
    calls.append(list(cmd))
    frame=float(cmd[cmd.index('-ss')+1])
    source=Path(cmd[cmd.index('-i')+1]).read_bytes()
    Path(cmd[-1]).write_bytes(b'PNG-'+source+b'-'+str(round(frame*30)).encode())
    return types.SimpleNamespace(returncode=0,stderr='',stdout='')
original=k.subprocess.run;k.subprocess.run=fake_run
def run_case(name,frame,expect_call):
    before=len(calls)
    try:
        result=k.stage_frame('S0021',frame,dst)
        content=b'PNG-'+k.SRC.read_bytes()+b'-'+str(frame).encode()
        passed=result==dst and dst.read_bytes()==content and (len(calls)>before)==expect_call
        cases.append({'name':name,'pass':passed,'extracted':len(calls)-before,'expected_extract':expect_call,'output_sha':hashlib.sha256(dst.read_bytes()).hexdigest()})
    except Exception as e:cases.append({'name':name,'pass':False,'error':repr(e)})
try:
    run_case('initial_extract',0,True)
    run_case('unchanged_reuse',0,False)
    k.SRC.write_bytes(b'SOURCE-B');run_case('source_same_path_size_mutation',0,True)
    k.SRC.write_bytes(b'SOURCE-A');run_case('source_restored_requires_current_output',0,True)
    k.SRC=src2;run_case('source_path_changed_same_bytes',0,True)
    run_case('frame_changed',1,True)
    dst.write_bytes(b'TAMPERED-FRAME');run_case('output_mutated',1,True)
finally:k.subprocess.run=original
rec={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':cases,'passed':sum(c['pass'] for c in cases),'total':len(cases),'boundary':'FFmpeg subprocess substituted by deterministic fixture; actual stage_frame and filesystem used. Worker must additionally prove real tiny FFmpeg extraction.'}
(out/'RESULT.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec));sys.exit(0 if all(c['pass'] for c in cases) else 1)

