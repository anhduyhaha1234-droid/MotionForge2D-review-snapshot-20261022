"""Read-only evidence for proposed C02; real copied cache/common/gate in isolated data."""
from pathlib import Path
import hashlib, importlib, json, sys
OUT=Path(__file__).resolve().parent
src=OUT/'preimages/run/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6/scripts'
out=OUT/'root-review/c02-baseline'
assert not out.exists()
out.mkdir(parents=True)
(out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
task=out/'fixture/task'; r6=task/'corrections/identity/r6'; scripts=r6/'scripts'
scripts.mkdir(parents=True)
hashes={}
for name in ['r6_common.py','r6_gate.py','r6_cache.py']:
    b=(src/name).read_bytes(); (scripts/name).write_bytes(b)
    hashes[name]=hashlib.sha256(b).hexdigest()
sid='S0021'
(task/'chunk_plan.json').write_text(json.dumps({'chunks':[{'unit_id':sid,'start_frame':2820,'frames':10}]}))
sys.dont_write_bytecode=True; sys.path.insert(0,str(scripts))
K=importlib.import_module('r6_common'); C=importlib.import_module('r6_cache'); G=importlib.import_module('r6_gate')
K.SRC.parent.mkdir(parents=True); K.SRC.write_bytes(b'isolated source bytes')
C.MODEL_PATH=out/'tiny-model.bin'; C.MODEL_PATH.write_bytes(b'isolated model bytes')
(r6/'source_actor_ledger.jsonl').write_text(json.dumps({'shot':sid,'n':10,'actors':[],'events':[],'contacts':[]})+'\n')
(r6/'storyboard'/f'{sid}.json').write_text(json.dumps({'zero_explicit':True,'n':10,'keys':[{'fid':1}]}))
wd=r6/'work'/sid; wd.mkdir(); (r6/'keys'/sid).mkdir()
key=r6/'keys'/sid/'f_0001_key.png'; key.write_bytes(b'isolated key hash only')
graph=out/'graph.json'; graph.write_text('{}')
producer_settings={'mode':'zero_shot_asset_restyle','steps':4} # actual r6_keygen_asset.py build_deps call
dep=C.build_deps(sid,1,{'source_span_lo':2820,'source_span_hi':2830,'gframe':2820,'casts':[],'masks':[],'graph':graph},producer_settings)
(wd/'f_0001.deps.json').write_text(json.dumps(dep))
G.write_review('keys',sid+'_f0001',key,G.key_inputs_now(sid,1,key),{'shot':sid,'fid':1},'PASS','Fixture only, no semantic acceptance',frames=[1])
result={'source_hashes':hashes,'empty_verify_deps':C.verify_deps({}),'missing_model_and_source':C.verify_deps({'casts':[],'masks':[]}),'complete_dep_positive':C.verify_deps(dep),'unchanged_asset_skip':C.skip_allowed(sid,1,key),'producer_settings':producer_settings,'consumer_settings':C.settings_now(sid,1),'scope':'C02 baseline only; source/model are tiny fixtures, no runtime/media writes'}
(out/'RESULT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
