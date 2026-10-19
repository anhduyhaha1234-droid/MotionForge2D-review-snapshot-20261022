from pathlib import Path
import datetime, hashlib, json, sys

OUT = Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
RUN = Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
R6 = RUN/'tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6'
sys.path.insert(0, str(RUN/'manager/tools'))
import invocation_runtime as rt

target = OUT/'C02A_PREFLIGHT.json'
assert not target.exists()
prior = json.loads((OUT/'root-review/PROTECTED_SCOPE_CHECK_02.json').read_text())
assert prior['ok']
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'task': 'CODEX-C02A-DEPENDENCY-VERIFICATION', 'old_owner': '/root/motionforge_c01_coder', 'old_owner_status': 'completed; frozen candidate02 independently APPROVED', 'next_owner': '/root/motionforge_c02a_coder', 'model': 'gpt-6-sol', 'reasoning': 'max', 'controller': rt.controller_status(), 'active_leases': rt.leases_status(), 'render_quiet': rt.probe_render_quiet(), 'files': [], 'new_test': str(R6/'tests/test_codex_c02a_dependency_verification.py')}
editable = {'scripts/r6_cache.py', 'scripts/r6_gate.py', 'tests/test_codex_c01_review_binding.py'}
paths = sorted(set((R6/'scripts').glob('*.py')) | set((R6/'tests').glob('*.py')))
for p in paths:
    b = p.read_bytes()
    digest = hashlib.sha256(b).hexdigest()
    rel = p.relative_to(R6).as_posix()
    snapshot = OUT/'preimages/c02a'/rel
    assert not snapshot.exists()
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(b)
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest
    rec['files'].append({'path': str(p), 'relative': rel, 'role': 'writable' if rel in editable else 'protected', 'sha256': digest, 'bytes': len(b), 'lines': len(b.splitlines()), 'snapshot': str(snapshot), 'attribution': 'external R6 run artifact; not tracked in MAIN/INTEGRATION; exact snapshot authority'})
assert next(f['sha256'] for f in rec['files'] if f['relative']=='scripts/r6_gate.py') == '4c3f7a7213f7761b7f5cbf53d7257bfd1c893e7f50d04d4ffda38a2e3cf13996'
assert next(f['sha256'] for f in rec['files'] if f['relative']=='tests/test_codex_c01_review_binding.py') == 'e2744bc198bc91fe71ce4b2afafb9682e427c17c7ac0c1207b3a7643dbf2d330'
rec['ok'] = not Path(rec['new_test']).exists() and not rec['active_leases'] and rec['render_quiet'][0] is True and rec['controller']['holder'] not in ('ALIVE', 'UNKNOWN')
target.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
assert rec['ok'], 'preflight blocked; no dispatch'
sp = OUT/'PROJECT_STATE.json'
state = json.loads(sp.read_text())
(OUT/'PROJECT_STATE_C01_APPROVED_PRE_C02A.json').write_text(json.dumps({**state, 'updated_utc': rec['utc'], 'status': 'C01_APPROVED', 'active_writer': False, 'checkpoint': 'c01-worker/candidate02/CHECKPOINT_R01.md', 'root_review': 'C01_REVIEW_02.md', 'candidate_manifest': 'c01-worker/candidate02/CANDIDATE_MANIFEST_R01.json'}, ensure_ascii=False, indent=2), encoding='utf-8')
state.update(updated_utc=rec['utc'], task=rec['task'], status='C02A_READY_TO_DISPATCH', owner=rec['next_owner'], active_writer=False, task_packet=str(OUT/'TASK_C02A.md'), checkpoint='C02A_PREFLIGHT.json', root_review='C01_REVIEW_02.md', candidate_manifest='c01-worker/candidate02/CANDIDATE_MANIFEST_R01.json', next_action='Dispatch fresh compact GPT-6 Sol Max C02A owner; one CPU writer; root independently reviews after terminal', resume_preflight='C02A_PREFLIGHT.json')
state['completed_tasks'] = [{'task': 'CODEX-C01-REVIEW-BINDING', 'verdict': 'APPROVED', 'review': 'C01_REVIEW_02.md', 'candidate': 'c01-worker/candidate02/CANDIDATE_MANIFEST_R01.json', 'root_probes': '30/30 + 3/3', 'root_module': '17/17'}]
state['roadmap'] = ['C02A strict recorded dependency verification/current-file gate', 'C02B complete producer capture/settings/reuse/staged-source freshness', 'Event/child outcome correctness', 'Evidence and media corrections after engineering gates', '300s pilot independent semantic acceptance', 'Tool integration and full-source scope after pilot approval']
sp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': rec['ok'], 'files': len(rec['files']), 'writable': sum(f['role']=='writable' for f in rec['files']), 'state': state['status'], 'preflight': str(target)}))
