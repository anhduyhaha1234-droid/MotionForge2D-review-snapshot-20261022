from pathlib import Path
import hashlib, json, subprocess, datetime, re

base = Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
out = base / 'outputs/motionforge-gemini-handoff-20261017'
old = base / 'outputs/motionforge-codex-takeover-20261015'
main = Path('C:/Users/Admin/MotionForge2D')
integration = Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION')
out.mkdir(parents=True, exist_ok=True)
backup = out / 'preimages'
backup.mkdir(exist_ok=True)

def record(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

before = []
for p in [main/'docs/pm/HERMES_AUTOPILOT_RULES.md', main/'docs/pm/CODEX_PM_HANDOFF.md', main/'docs/pm/ROADMAP.md', old/'PROJECT_STATE.json']:
    dest = backup / p.name
    if dest.exists():
        raise RuntimeError('Preimage already exists; refuse to overwrite: '+str(dest))
    dest.write_bytes(p.read_bytes())
    before.append({**record(p), 'preimage': str(dest)})

cp = json.loads((old/'c02b2-worker/CHECKPOINT_015.json').read_text(encoding='utf-8-sig'))
current = []
for f in cp['files']:
    r = record(Path(f['path']))
    r['checkpoint_sha256'] = f['sha256']
    r['matches_checkpoint'] = r['sha256'] == f['sha256']
    current.append(r)
assert all(f['matches_checkpoint'] for f in current)

repos = []
for repo in [main, integration]:
    head = subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    status = subprocess.run(['git','-C',str(repo),'status','--porcelain=v1'],check=True,capture_output=True,text=True).stdout
    dest = out / ('MAIN_STATUS.txt' if repo == main else 'INTEGRATION_STATUS.txt')
    dest.write_text(status,encoding='utf-8')
    repos.append({'path':str(repo),'head':head,'dirty':bool(status.strip()),'status_file':str(dest)})
auto = Path('C:/Users/Admin/.codex/automations/motionforge-checkpoint-v-quota/automation.toml').read_text(encoding='utf-8')
status = re.search(r'^status\s*=\s*"([^"]+)"',auto,re.M).group(1)
assert status == 'PAUSED'
receipt = {
  'schema':1, 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'purpose':'Prepare user-carried Gemini prompt; not a dispatch or owner transfer',
  'handoff_status':'PREPARED_NOT_DISPATCHED', 'automation_status':status,
  'project_state_status':json.loads((old/'PROJECT_STATE.json').read_text(encoding='utf-8-sig'))['status'],
  'previous_worker_tool_status':'/root/motionforge_c02b2_coder terminal errored: usage limit (collaboration.list_agents this turn)',
  'other_existing_worker':'/root/motionforge_c02b1_coder completed',
  'os_process_queue_lease_audit':'NOT_PERFORMED_FOR_PROMPT_PREPARATION; mandatory fresh check before new writer',
  'model':'ag/gemini-3.8-flash-high', 'base_url':'http://127.0.0.1:20128/v1',
  'gateway_proof':'../9router-gemini-20261016/FINAL_STATUS.json; prior live test, not re-run for this document',
  'preimages':before,'current_c02b2_files':current,'repositories':repos,
  'changes_allowed_this_turn':'Handoff documents and PM index/rules only; no production code, media, runtime, model or automation change'
}
(out/'HANDOFF_PREFLIGHT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'out':str(out),'checkpoint_files_match':len(current),'automation':status,'repositories':repos},ensure_ascii=False))
