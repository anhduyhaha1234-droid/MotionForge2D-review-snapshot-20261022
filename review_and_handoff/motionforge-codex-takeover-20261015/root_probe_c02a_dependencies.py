"""Independent C02A probes; real copied modules, tiny isolated dependencies only."""
from pathlib import Path
import argparse, copy, datetime, hashlib, importlib, json, sys

ap = argparse.ArgumentParser()
ap.add_argument("--scripts", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
src, out = Path(a.scripts).resolve(), Path(a.out).resolve()
assert not out.exists(), "fresh evidence path required"
out.mkdir(parents=True)
probe = Path(__file__).read_bytes()
(out/"probe_source.py").write_bytes(probe)
task = out/"fixture/task"
r6 = task/"corrections/identity/r6"
sd = r6/"scripts"
sd.mkdir(parents=True)
hashes = {}
for name in ("r6_common.py", "r6_cache.py", "r6_gate.py", "r6_assemble.py"):
    b = (src/name).read_bytes()
    (sd/name).write_bytes(b)
    hashes[name] = hashlib.sha256(b).hexdigest()
sid, fid = "S0021", 1
(task/"chunk_plan.json").write_text(json.dumps({"chunks":[{"unit_id":sid,"start_frame":2820,"frames":9000}]}), encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, str(sd))
K = importlib.import_module("r6_common")
C = importlib.import_module("r6_cache")
G = importlib.import_module("r6_gate")
K.SRC.parent.mkdir(parents=True)
K.SRC.write_bytes(b"source01")
C.MODEL_PATH = out/"tiny-model.bin"
C.MODEL_PATH.write_bytes(b"model001")
wd = r6/"work"/sid
wd.mkdir(parents=True)
cast = out/"cast.bin"; cast.write_bytes(b"cast0001")
mask = out/"mask.bin"; mask.write_bytes(b"mask0001")
graph = out/"graph.json"; graph.write_bytes(b'{"g":1}')
row = {"shot":sid,"src":[2820,11820],"n":9000,"zero_explicit":False,"actors":[],"events":[],"contacts":[]}
(r6/"source_actor_ledger.jsonl").write_text(json.dumps(row)+"\n", encoding="utf-8")
(r6/"storyboard"/(sid+".json")).write_text(json.dumps({"zero_explicit":False,"n":9000,"keys":[{"fid":1}]}), encoding="utf-8")
key = r6/"keys"/sid/"f_0001_key.png"
key.parent.mkdir(parents=True)
key.write_bytes(b"key00001")
consumed = {"source_span_lo":2820,"source_span_hi":11820,"gframe":2820,"casts":[cast],"masks":[mask],"graph":graph}
settings = {"model":"flux-2-klein-4b-fp8","steps":4,"sampler":"euler","cfg":1.0,"seed":2026122401}
base = C.build_deps(sid, fid, consumed, settings)
dp = wd/"f_0001.deps.json"
rp = G.REV/"keys"/(sid+"_f0001.review.json")
results = []

def seal(dep):
    dep = copy.deepcopy(dep)
    dep.pop("deps_sha", None)
    dep["deps_sha"] = hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()
    return dep

def save(dep, raw=None):
    dp.write_text(json.dumps(dep) if raw is None else raw, encoding="utf-8")
    # Bind a review to the exact supplied record without invoking the consumer validator.
    # This isolates dependency validity from the already-approved C01 hash comparison.
    inputs = {"ledger_row_sha":G.ledger_row_sha(sid), "deps_sha":hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()}
    G.write_review("keys",sid+"_f0001",key,inputs,{"shot":sid,"fid":fid},"PASS","isolated dependency integrity fixture",reviewer="root-independent",frames=[1])

def case(label, fn, expected="BLOCK"):
    try:
        val = fn()
        if isinstance(val, tuple) and len(val)==2 and type(val[0]) is bool:
            actual, detail = ("ACCEPT" if val[0] else "BLOCK"), str(val[1])
        else:
            actual, detail = "ACCEPT", ""
    except G.GateBlock as e:
        actual, detail = "BLOCK", str(e)
    except Exception as e:
        actual, detail = "UNCONTROLLED_EXCEPTION", repr(e)
    results.append({"name":label,"expected":expected,"actual":actual,"pass":actual==expected,"detail":detail})

case("builder_v3_positive",lambda:C.verify_deps(base),"ACCEPT")
passthrough = C.build_deps(sid,fid,{**consumed,"casts":[],"masks":[],"graph":None},{"mode":"keep_source_no_visible_actor"})
case("builder_passthrough_positive",lambda:C.verify_deps(passthrough),"ACCEPT")
for label, bad in [("empty",{}),("list",[]),("none",None),("string","oops")]:
    case("verify_"+label,lambda bad=bad:C.verify_deps(bad))
for field in ("kind","shot","fid","source","model","casts","masks","graph","settings","deps_sha"):
    dep = copy.deepcopy(base)
    dep.pop(field)
    if field!="deps_sha": dep=seal(dep)
    case("verify_missing_"+field,lambda dep=dep:C.verify_deps(dep))
for field, val in (("fid",True),("fid",0),("casts",{}),("masks",None),("settings",{}),("settings",[]),("graph",None)):
    dep = copy.deepcopy(base); dep[field] = val; dep = seal(dep)
    case("verify_bad_"+field+"_"+repr(val),lambda dep=dep:C.verify_deps(dep))
for group, field, val in (("source","sha256",""),("model","sha256",False),("source","gframe",True),("source","span",[2820]),("model","path","bad\x00path")):
    dep=copy.deepcopy(base);dep[group][field]=val;dep=seal(dep)
    case("verify_bad_"+group+"_"+field,lambda dep=dep:C.verify_deps(dep))
tamper=copy.deepcopy(base);tamper["settings"]["steps"]=5
case("verify_self_digest_tamper",lambda:C.verify_deps(tamper))
save(base)
case("gate_key_unchanged_positive",lambda:G.gate_key(sid,fid),"ACCEPT")
for label, path in (("source",K.SRC),("model",C.MODEL_PATH),("cast",cast),("mask",mask),("graph",graph)):
    before=path.read_bytes()
    path.write_bytes(bytes([before[0]^1])+before[1:])
    case("verify_same_path_size_mutation_"+label,lambda:C.verify_deps(base))
    case("gate_same_path_size_mutation_"+label,lambda:G.gate_key(sid,fid))
    path.write_bytes(before)
case("gate_restored_positive",lambda:G.gate_key(sid,fid),"ACCEPT")
alternate_source=out/"same-bytes-source.bin";alternate_source.write_bytes(K.SRC.read_bytes())
alternate_model=out/"same-bytes-model.bin";alternate_model.write_bytes(C.MODEL_PATH.read_bytes())
mutations=[
    ("kind",lambda d:d.update(kind="r6_key_deps_v2")),
    ("shot",lambda d:d.update(shot="S0022")),
    ("fid",lambda d:d.update(fid=2)),
    ("source_path",lambda d:d["source"].update(path=str(alternate_source))),
    ("model_path",lambda d:d["model"].update(path=str(alternate_model))),
    ("gframe",lambda d:d["source"].update(gframe=2821)),
    ("span",lambda d:d["source"].update(span=[2820,11821])),
    ("combined",lambda d:(d.update(shot="S0022",fid=2),d["source"].update(gframe=2821,span=[2821,11821]))),
    ("missing_source_hash",lambda d:d["source"].pop("sha256")),
]
for label, mut in mutations:
    dep=copy.deepcopy(base);mut(dep);dep=seal(dep);save(dep)
    case("consumer_identity_"+label,lambda:G.gate_key(sid,fid))
for label, raw in [("invalid_json","{"),("duplicate_field",json.dumps(base)[:-1]+', "fid":1}'),("non_json_constant",json.dumps(base)[:-1]+', "stray":NaN}')]:
    save(base,raw)
    case("consumer_"+label,lambda:G.gate_key(sid,fid))

# Real assembly entry must reject stale dependencies before its copy/encoder boundary.
save(base)
A=importlib.import_module("r6_assemble")
calls=[]
def tripwire(*args,**kwargs):
    calls.append(repr(args))
    raise AssertionError("copy/encoder reached")
A.shutil.copyfile=tripwire
K.run=tripwire
before=K.SRC.read_bytes();K.SRC.write_bytes(b"changed1")
def assemble():
    try: A.main()
    except G.GateBlock as e:
        if "BLEND_" in str(e):
            raise AssertionError("stale key passed; blocked only at later blend gate: "+str(e))
        raise
case("actual_assembler_stale_source_before_copy_encode",assemble)
K.SRC.write_bytes(before)
if calls:
    results.append({"name":"no_encoder_copy_calls","expected":"NONE","actual":calls,"pass":False})
# Full gate positive uses a three-frame isolated blend; no video/decode claim.
save(base)
bd=wd/"blend";bd.mkdir()
frames=[]
for i in range(1,4):
    p=bd/f"{i:04d}.jpg";p.write_bytes(f"fixture {i}".encode())
    frames.append({"name":p.name,"size":p.stat().st_size,"sha256":K.sha(p)})
man=wd/"blend_manifest.json"
man.write_text(json.dumps({"frames":frames,"blend_dir":str(bd),"child_outcomes":[{"rc":0}],"decode_ok":True,"key_set_sha":"c"*64,"child_outcomes_sha":"d"*64}),encoding="utf-8")
G.write_review("blend",sid+"_blend",man,G.blend_inputs_now(sid),{"shot":sid,"frames":3},"PASS","isolated frame binding only",frames=[1,2,3])
case("real_gate_assemble_valid_positive",lambda:G.gate_assemble([(sid,3)]),"ACCEPT")
receipt={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source_hashes":hashes,"probe_source_sha256":hashlib.sha256(probe).hexdigest(),"cases":results,"passed":sum(x["pass"] for x in results),"total":len(results),"side_effect_calls":calls,"scope":"Recorded dependency verification only; no producer completeness, reuse, semantic or decode proof."}
(out/"RESULT.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
print(json.dumps({"passed":receipt["passed"],"total":receipt["total"],"failures":[x for x in results if not x["pass"]],"receipt":str(out/"RESULT.json")}))
raise SystemExit(0 if all(x["pass"] for x in results) else 1)

