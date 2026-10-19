from pathlib import Path
import json, hashlib, datetime, shutil, urllib.request
O=Path(r'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014')
A=json.loads((O/'AUDIT.json').read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
S=O/'snapshot/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6/scripts'
patterns={'r6_assemble.py':['def main','got <','"-ss", "300"'],
 'r6_gate.py':['def require_review','for k, v','missing_ev =','newest =','def gate_assemble'],
 'r6_propagate.py':['for fid in range(1','newest =','completed:'],
 'r6_cotracker.py':['T = min','events =','qs.append'],
 'r6_cache.py':['def build_deps','def verify_deps','def skip_allowed'],
 'r6_matrix.py':['R("Q'], 'r6_qa.py':['evs =','ef =','rec =']}
loc={n:[{'line':i,'text':l.strip()} for i,l in enumerate((S/n).read_text(encoding='utf-8').splitlines(),1) if any(x in l for x in vals)] for n,vals in patterns.items()}
(O/'FINDING_LOCATIONS.json').write_text(json.dumps(loc,indent=2),encoding='utf-8')
guard={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_drift':[], 'snapshot_input_drift':[],'media':{},'pm_changes':[]}
pmnames={'HERMES_AUTOPILOT_RULES.md','CODEX_PM_HANDOFF.md','ROADMAP.md'}
for s,v in A['protected'].items():
    p=Path(s);actual=sha(p) if p.exists() else None
    if actual!=v.get('sha256'):
        item={'path':s,'before':v.get('sha256'),'after':actual}
        if p.name in pmnames:
            old=(O/'preimages'/p.name).read_bytes();new=p.read_bytes()
            item.update({'before_bytes':len(old),'after_bytes':len(new),'before_lines':len(old.splitlines()),'after_lines':len(new.splitlines()),'preimage':str(O/'preimages'/p.name)})
            guard['pm_changes'].append(item)
        else:guard['protected_drift'].append(item)
for s,v in A['snapshots'].items():
    p=Path(s);actual=sha(p) if p.exists() else None
    if actual!=v.get('sha256'):guard['snapshot_input_drift'].append({'path':s,'before':v['sha256'],'after':actual})
for n,v in A['media'].items():
    actual=sha(Path(v['path']));guard['media'][n]={'sha256':actual,'stable':actual==v['sha256']}
try:
    with urllib.request.urlopen('http://127.0.0.1:8188/queue',timeout=5) as f:guard['final_queue']=json.load(f)
except Exception as e:guard['final_queue']={'unknown':str(e)}
guard['db_read_only_guard']=A['db_guard']
prompt=(O/'NEXT_HERMES_MANAGER_PROMPT.md').read_text(encoding='utf-8')
guard['prompt_checks']={'starts_rules_load':prompt.startswith('Đọc TOÀN BỘ C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md'),
 'exact_worker':'20261007_234033_cc0b6d' in prompt,'exact_manager':'20261012_002032_daa36c' in prompt,'no_reset':'cumulative counters' in prompt,
 'twelve_rows_all_present':all(f'Q{i:02d}' in prompt for i in range(1,13)),'full22_blocked':'BLOCKED_DEPENDENCY' in prompt,
 'matching_proposal':(O/'SESSION_OPENING_PROPOSAL.md').exists()}
assert not guard['protected_drift'] and not guard['snapshot_input_drift'],guard
assert all(v['stable'] for v in guard['media'].values())
assert len(guard['pm_changes'])==3
assert all(guard['prompt_checks'].values())
(O/'FINAL_GUARD.json').write_text(json.dumps(guard,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(Path(__file__),O/Path(__file__).name)
manifest={'utc':guard['utc'],'note':'Review outputs only, manifest excludes itself. Run artifacts are read-only and bound in AUDIT/FINAL_GUARD.','files':[]}
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='PACKET_MANIFEST.json':manifest['files'].append({'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)})
(O/'PACKET_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'locations':loc,'guard':{'protected_drift':guard['protected_drift'],'snapshot_input_drift':guard['snapshot_input_drift'],'pm_changed':[p['path'] for p in guard['pm_changes']],'media':guard['media'],'prompt_checks':guard['prompt_checks']},'packet_files':len(manifest['files'])},ensure_ascii=True,indent=2))
