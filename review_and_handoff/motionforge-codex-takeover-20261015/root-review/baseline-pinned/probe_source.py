"""Independent C01 review probes; copied real modules run only inside new fixtures."""
from pathlib import Path
import argparse, copy, hashlib, importlib, json, shutil, sys, datetime

ap=argparse.ArgumentParser()
ap.add_argument('--scripts',required=True)
ap.add_argument('--out',required=True)
args=ap.parse_args()
src=Path(args.scripts).resolve(); out=Path(args.out).resolve()
assert not out.exists(), 'fresh output only'
out.mkdir(parents=True)
probe_source=Path(__file__).read_bytes()
(out/'probe_source.py').write_bytes(probe_source)
task=out/'fixture/task'; r6=task/'corrections/identity/r6'; scripts=r6/'scripts'
scripts.mkdir(parents=True)
hashes={}
for n in ['r6_common.py','r6_gate.py','r6_assemble.py']:
    b=(src/n).read_bytes(); (scripts/n).write_bytes(b); hashes[n]=hashlib.sha256(b).hexdigest()
sid='S0021'
(task/'chunk_plan.json').write_text(json.dumps({'chunks':[{'unit_id':sid,'start_frame':2820,'frames':9000}]}),encoding='utf-8')
sys.dont_write_bytecode=True
sys.path.insert(0,str(scripts))
K=importlib.import_module('r6_common'); G=importlib.import_module('r6_gate')
row={'shot':sid,'n':9000,'actors':[],'events':[],'contacts':[]}
(r6/'source_actor_ledger.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
(r6/'storyboard'/f'{sid}.json').write_text(json.dumps({'keys':[{'fid':1}]}),encoding='utf-8')
(r6/'keys'/sid).mkdir()
(r6/'work'/sid).mkdir()
artifact=r6/'keys'/sid/'f_0001_key.png'; artifact.write_bytes(b'fixture bytes, hash integrity only')
dep=r6/'work'/sid/'f_0001.deps.json'; dep.write_text('{"model_sha":"pinned-model-fixture"}',encoding='utf-8')
inputs=G.key_inputs_now(sid,1,artifact)
rp=G.write_review('keys',sid+'_f0001',artifact,inputs,{'shot':sid,'fid':1},'PASS','Fixture review evidence; not semantic proof',reviewer='root-independent-probe',frames=[1])
base=json.loads(rp.read_text(encoding='utf-8'))
cases=[]
def run(name, mutate=None, current=None, raw=None, expected='BLOCK'):
    rec=copy.deepcopy(base)
    if mutate: mutate(rec)
    rp.write_text(json.dumps(rec) if raw is None else raw,encoding='utf-8')
    try:
        G.require_review('keys',sid+'_f0001',artifact,inputs if current is None else current)
        actual='ACCEPT'; detail=''
    except G.GateBlock as e: actual='BLOCK'; detail=str(e)
    except Exception as e: actual='UNCONTROLLED_EXCEPTION'; detail=type(e).__name__+': '+str(e)
    cases.append({'name':name,'expected':expected,'actual':actual,'pass':actual==expected,'detail':detail})

run('valid_current_record',expected='ACCEPT')
run('review_omits_current_dependency',lambda r:r['inputs'].pop('deps_sha'))
run('review_unknown_dependency',lambda r:r['inputs'].update({'unrecognized':'value'}))
run('changed_current_dependency',current={**inputs,'deps_sha':'changed'})
run('empty_current_binding',current={})
run('empty_record_binding',lambda r:r.update(inputs={}))
run('wrong_review_id',lambda r:r.update(review_id='keys:S0022_f0001'))
other=artifact.with_name('same_bytes_other.png'); other.write_bytes(artifact.read_bytes())
run('other_artifact_path_same_bytes',lambda r:r['artifact'].update(path=str(other)))
run('wrong_artifact_hash',lambda r:r['artifact'].update(sha256='0'*64))
run('malformed_frames_strings',lambda r:r.update(frames=['unviewed']))
run('malformed_frames_bool',lambda r:r.update(frames=[True]))
run('malformed_reviewer_numeric',lambda r:r.update(reviewer=7))
run('malformed_evidence_list',lambda r:r.update(evidence=['no textual review']))
run('missing_verdict',lambda r:r.pop('verdict'))
run('unknown_verdict',lambda r:r.update(verdict='UNKNOWN'))
run('json_array_record',raw='[]')
run('invalid_json',raw='{')
run('numeric_hash_in_both_bindings',lambda r:r['inputs'].update(deps_sha=5),current={**inputs,'deps_sha':5})
run('null_hash_in_both_bindings',lambda r:r['inputs'].update(deps_sha=None),current={**inputs,'deps_sha':None})
run('bool_hash_in_both_bindings',lambda r:r['inputs'].update(deps_sha=True),current={**inputs,'deps_sha':True})
run('malformed_artifact_array',lambda r:r.update(artifact=[]))
run('null_artifact_path',lambda r:r['artifact'].update(path=None))
run('nul_artifact_path',lambda r:r['artifact'].update(path='bad\x00path'))
run('empty_expected',lambda r:r.update(expected={}))
run('malformed_expected_array',lambda r:r.update(expected=[]))
run('malformed_frame_zero',lambda r:r.update(frames=[0]))
run('malformed_frame_float',lambda r:r.update(frames=[1.0]))
run('missing_artifact_hash',lambda r:r['artifact'].pop('sha256'))
run('missing_review_timestamp',lambda r:r.pop('reviewed_at'))

# Invoke real assemble main. All planned geometry is valid, but its sole key review
# omits the dependency. If the public path accepts it, it reaches our copy tripwire
# (other gate stages supplied realistic manifests are covered by coder tests).
# For this probe, any failure outside the key gate is evidence the bad review leaked.
rp.write_text(json.dumps({**base,'inputs':{'ledger_row_sha':inputs['ledger_row_sha']}}),encoding='utf-8')
A=importlib.import_module('r6_assemble')
calls=[]
def tripwire(*a,**kw): calls.append(str(a)); raise AssertionError('encoder/copy reached')
A.shutil.copyfile=tripwire
K.run=tripwire
try:
    A.main(); actual='ACCEPT'; detail=''
except G.GateBlock as e:
    detail=str(e)
    actual='BLOCK_AT_REVIEW' if ('INPUT' in detail or 'BINDING' in detail) else 'BLOCK_LATER'
except Exception as e: actual='UNCONTROLLED_EXCEPTION'; detail=type(e).__name__+': '+str(e)
cases.append({'name':'actual_assembly_rejects_omitted_review_input','expected':'BLOCK_AT_REVIEW','actual':actual,'pass':actual=='BLOCK_AT_REVIEW' and not calls,'detail':detail,'side_effect_calls':calls})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'probe_source_sha256':hashlib.sha256(probe_source).hexdigest(),'scripts':str(src),'source_hashes':hashes,'cases':cases,'passed':sum(c['pass'] for c in cases),'total':len(cases)}
(out/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'passed':result['passed'],'total':result['total'],'failures':[c for c in cases if not c['pass']],'receipt':str(out/'RESULT.json')}))
sys.exit(0 if all(c['pass'] for c in cases) else 1)
