"""Probe parsed JSON nesting through verification, not only the JSON parser."""
from pathlib import Path
import argparse, hashlib, importlib, json, sys
ap=argparse.ArgumentParser();ap.add_argument("--scripts",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
src=Path(a.scripts);out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True)
(out/"probe_source.py").write_bytes(Path(__file__).read_bytes())
task=out/"task";r6=task/"corrections/identity/r6";sd=r6/"scripts";sd.mkdir(parents=True)
hashes={}
for name in ("r6_common.py","r6_cache.py","r6_gate.py"):
 b=(src/name).read_bytes();(sd/name).write_bytes(b);hashes[name]=hashlib.sha256(b).hexdigest()
(task/"chunk_plan.json").write_text(json.dumps({"chunks":[{"unit_id":"S0021","start_frame":2820,"frames":3}]}))
sys.dont_write_bytecode=True;sys.path.insert(0,str(sd))
K=importlib.import_module("r6_common");C=importlib.import_module("r6_cache");G=importlib.import_module("r6_gate")
K.SRC.parent.mkdir(parents=True);K.SRC.write_bytes(b"tiny source")
C.MODEL_PATH=out/"model.bin";C.MODEL_PATH.write_bytes(b"tiny model")
graph=out/"graph.json";graph.write_text("{}")
(r6/"source_actor_ledger.jsonl").write_text(json.dumps({"shot":"S0021","n":3,"actors":[],"events":[],"contacts":[]})+"\n")
key=r6/"keys/S0021/f_0001_key.png";key.parent.mkdir();key.write_bytes(b"key")
dp=r6/"work/S0021/f_0001.deps.json";dp.parent.mkdir()
base=C.build_deps("S0021",1,{"source_span_lo":2820,"source_span_hi":2823,"gframe":2820,"casts":[],"masks":[],"graph":graph},{"steps":4})
cases=[]
for depth in (10,200,400,800):
 dep=json.loads(json.dumps(base));nested=0
 for i in range(depth):nested=[nested]
 dep["settings"]["nested"]=nested
 body={k:v for k,v in dep.items() if k!="deps_sha"}
 dep["deps_sha"]=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
 raw=json.dumps(dep);dp.write_text(raw)
 loaded,why=C.load_deps(dp)
 inputs={"ledger_row_sha":G.ledger_row_sha("S0021"),"deps_sha":hashlib.sha256(json.dumps(dep,sort_keys=True).encode()).hexdigest()}
 G.write_review("keys","S0021_f0001",key,inputs,{"shot":"S0021","fid":1},"PASS","nesting fixture only",frames=[1])
 for lane,fn in (("verify",lambda:C.verify_deps(loaded,"S0021",1)),("gate_key",lambda:G.gate_key("S0021",1))):
  try:
   val=fn();actual="BLOCK" if isinstance(val,tuple) and val[0] is False else "ACCEPT";detail=str(val[1]) if isinstance(val,tuple) else ""
  except G.GateBlock as e:actual="BLOCK";detail=str(e)
  except Exception as e:actual="UNCONTROLLED_EXCEPTION";detail=repr(e)
  expected="ACCEPT" if depth==10 else "CONTROLLED"
  cases.append({"depth":depth,"lane":lane,"loader_result":why,"expected":expected,"actual":actual,"pass":actual=="ACCEPT" if depth==10 else actual in ("ACCEPT","BLOCK"),"detail":detail})
rec={"source_hashes":hashes,"cases":cases,"passed":sum(x["pass"] for x in cases),"total":len(cases)}
(out/"RESULT.json").write_text(json.dumps(rec,indent=2));print(json.dumps(rec))
raise SystemExit(0 if all(x["pass"] for x in cases) else 1)

