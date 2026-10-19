import copy, datetime, importlib.util, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]/'outputs'/'motionforge-video-skills-20261012'
SKILL=ROOT/'motionforge-video-craft'
script=SKILL/'scripts'/'validate_cues.py'
spec=importlib.util.spec_from_file_location('cue_reference',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
base=json.loads((SKILL/'assets'/'cue-plan.example.json').read_text(encoding='utf-8'))
cases=[]
def check(name,modify,expected=None):
    value=copy.deepcopy(base)
    modify(value)
    errors=module.validate(value)
    ok=not errors if expected is None else any(expected in e for e in errors)
    cases.append({'name':name,'passed':ok,'errors':errors,'expected_error':expected})
check('synthetic source-locked valid',lambda p:None)
check('fractional rate retains exact frame count',lambda p:p.update(fps_num=30000,fps_den=1001))
check('bool is not a frame rate',lambda p:p.update(fps_num=True),'FPS_NUM_INVALID')
check('zero denominator',lambda p:p.update(fps_den=0),'FPS_DEN_INVALID')
check('locked missing last frame',lambda p:p.update(output_frame_count=299),'SOURCE_LOCK_FRAME_COUNT_MISMATCH')
check('locked cut forbidden',lambda p:p['cues'][0].update(action='cut'),'SOURCE_LOCK_MUTATION_FORBIDDEN')
check('locked overlay forbidden',lambda p:p['cues'][0].update(action='graphic'),'SOURCE_LOCK_MUTATION_FORBIDDEN')
check('locked audio rewrite forbidden',lambda p:p.update(audio_policy='authored_mix'),'SOURCE_LOCK_POLICY_VIOLATION')
check('cue outside final boundary',lambda p:p['cues'][0].update(start_frame=300,end_frame=301),'FRAME_RANGE_INVALID')
check('fractional frame forbidden',lambda p:p['cues'][0].update(start_frame=1.5),'FRAME_RANGE_INVALID')
check('last frame valid',lambda p:p['cues'][0].update(start_frame=299,end_frame=300))
check('duplicate cue id',lambda p:p['cues'].append(copy.deepcopy(p['cues'][0])),'ID_DUPLICATE')
check('stale source evidence',lambda p:p['cues'][0]['evidence'].update(asset_sha256='b'*64),'SOURCE_EVENT_HASH_MISMATCH')
def word(p,method):
    p.update(mode='launch',audio_policy='authored_mix',frame_map_policy='authored')
    p['cues'][0].update(clock='word',action='caption')
    p['cues'][0]['evidence'].update(timing_method=method)
check('measured launch word',lambda p:word(p,'measured'))
check('estimated word cannot claim sync',lambda p:word(p,'estimated'),'WORD_TIMING_NOT_MEASURED')
check('missing evidence',lambda p:p['cues'][0].pop('evidence'),'EVIDENCE_REQUIRED')
check('unrecognized extra field',lambda p:p.update(auto_approve=True),'PLAN_FIELDS_MISMATCH')
check('unknown mode fails closed',lambda p:p.update(mode='magic'),'MODE_INVALID')
check('malformed mode list fails closed',lambda p:p.update(mode=[]),'MODE_INVALID')
check('footage edit requires mapped audio',lambda p:p.update(mode='footage_edit'),'EDIT_MAP_REQUIRED')
cli=subprocess.run([sys.executable,str(script),str(SKILL/'assets'/'cue-plan.example.json')],text=True,capture_output=True)
assert cli.returncode==0,cli.stderr
assert all(c['passed'] for c in cases),cases
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'synthetic reference contract only; no MotionForge production import or media render','passed':len(cases),'total':len(cases),'cases':cases,'cli_exit_code':cli.returncode,'cli_result':json.loads(cli.stdout),'production_test_suite_run':False,'video_quality_verified':False}
(ROOT/'CONTRACT_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(cases),'total':len(cases),'cli_exit_code':cli.returncode}))
