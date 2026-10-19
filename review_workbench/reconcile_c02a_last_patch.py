from pathlib import Path
import datetime, hashlib, json
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
prior=json.loads((OUT/'RESUME_PREFLIGHT_C02A_20261016T0909.json').read_text())
f=next(x for x in prior['files'] if Path(x['path']).name=='test_codex_c02a_dependency_verification.py')
b=Path(f['path']).read_bytes()
after=b'                self.assert_invalid(label, self.changed(\n                    base, path, value, reseal=label != "deps_sha_bool"))'
before=b'                self.assert_invalid(label, self.changed(base, path, value))'
assert b.count(after)==1
reverse=b.replace(after,before,1)
patch05=json.loads((OUT/'c02a-worker/PATCH_05.json').read_text(encoding='utf-8-sig'))
proof=hashlib.sha256(reverse).hexdigest()==patch05['sha256']
stable=all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in prior['files'])
ok=proof and stable and not prior['unexpected_changes'] and not prior['active_leases'] and prior['render_quiet'][0] is True and prior['controller']['holder'] not in ('ALIVE','UNKNOWN')
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':ok,'prior_preflight':'RESUME_PREFLIGHT_C02A_20261016T0909.json','quota_receipt':'QUOTA_RESUME_20261016T0909.json','owner':'/root/motionforge_c02a_coder','model':'gpt-6-sol','reasoning':'max','all_28_files_stable':stable,'unreceipted_test_patch':{'current_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'lines':len(b.splitlines()),'reverse_one_bounded_callsite_edit_sha256':hashlib.sha256(reverse).hexdigest(),'matches_patch05_exact':proof,'explanation':'One call site adds reseal=False for deps_sha_bool, preserving the deliberately malformed digest rather than overwriting it with a valid digest. Existing assert_invalid/assertFalse is unchanged. The reverse bytes exactly match PATCH_05; no source restoration or production write performed.'},'next_action':'Same owner resume existing C02A packet; validate last input-fixture correction then complete remaining integration/C01 tests and self-review. Do not restart earlier work or broaden scope.'}
target=OUT/'RESUME_RECONCILIATION_C02A_20261016T0913.json';assert not target.exists();target.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
assert ok
state=json.loads((OUT/'PROJECT_STATE.json').read_text(encoding='utf-8-sig'));state.update(updated_utc=rec['utc'],status='C02A_READY_TO_RESUME_AFTER_QUOTA',active_writer=False,checkpoint=target.name,resume_preflight=target.name,next_action=rec['next_action'])
(OUT/'PROJECT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rec))
