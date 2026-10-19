from pathlib import Path
import hashlib, json, shutil, sqlite3, datetime

BASE = Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
EX = BASE/'outputs/motionforge-gemini-handoff-20261017/execution'
G1 = EX/'submissions/g1-candidate-01'
OUT = BASE/'outputs/motionforge-g1-review-20261018'
OUT.mkdir(exist_ok=True)
manifest = json.loads((G1/'MANIFEST.json').read_text(encoding='utf-8-sig'))
R6 = Path(manifest['files'][0]['path']).parents[1]
SNAP = OUT/'candidate/task/corrections/identity/r6'
def sha(data): return hashlib.sha256(data).hexdigest()
def copy(src, dst):
    data=src.read_bytes(); dst.parent.mkdir(parents=True,exist_ok=True)
    assert not dst.exists(), f'refusing overwrite: {dst}'
    dst.write_bytes(data)
    return data
receipt=[]
for f in manifest['files']:
    src=Path(f['path']); data=src.read_bytes(); live_sha=sha(data)
    if live_sha != f['sha256']:
        copy(src, OUT/'observed_live'/f['relative'])
        src=EX/'A4/probe_v4_result/task/corrections/identity/r6'/f['relative']
        data=src.read_bytes()
    assert sha(data)==f['sha256'], f'candidate unavailable: {f["relative"]}'
    dst=SNAP/f['relative']; copy(src,dst)
    receipt.append(dict(relative=f['relative'], expected_sha256=f['sha256'], snapshot_sha256=sha(data),
        live_sha256=live_sha, live_matches=(live_sha==f['sha256']), snapshot=str(dst), source=str(src)))
deps=[]
sources=list((R6/'scripts').glob('*.py')) + [R6/'tests'/n for n in (
    'test_codex_c01_review_binding.py','test_codex_c02a_dependency_verification.py','test_codex_c02b1_staged_source.py')]
for src in sources:
    dst=SNAP/src.relative_to(R6)
    if dst.exists(): continue
    data=copy(src,dst)
    deps.append(dict(source=str(src),snapshot=str(dst),sha256=sha(data),bytes=len(data)))
vendor=R6.parent/'r5/vendor/cropandstitch_8584b08d'
for src in vendor.rglob('*.py'):
    dst=SNAP.parent/'r5/vendor/cropandstitch_8584b08d'/src.relative_to(vendor)
    data=copy(src,dst); deps.append(dict(source=str(src),snapshot=str(dst),sha256=sha(data),bytes=len(data)))
copy(R6.parents[2]/'chunk_plan.json',SNAP.parents[2]/'chunk_plan.json')
for src in G1.iterdir():
    if src.is_file(): copy(src,OUT/'submitted_packet'/src.name)
for name in ('STATE.json','CHECKPOINT.json','RESUME.md'):
    src=EX/name
    if src.exists(): copy(src,OUT/'observed_execution'/name)
authority=Path('C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md')
copy(authority,OUT/'authority/HERMES_AUTOPILOT_RULES.md')
result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), submission='g1-candidate-01',
    scope='Exact 14 manifest file bytes; remaining dependencies observed at review time (not bound by submitted manifest).',
    files=receipt,dependencies=deps,authority_sha256=sha(authority.read_bytes()))
(OUT/'CANDIDATE_IDENTITY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
db=sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro',uri=True)
db.execute('PRAGMA query_only=ON')
db.row_factory=sqlite3.Row
session='20261017_115944_b2a338'
cols=[r[1] for r in db.execute('pragma table_info(messages)')]
print('messages_columns',cols)
rows=[dict(r) for r in db.execute('SELECT * FROM messages WHERE session_id=? AND role=? ORDER BY id DESC LIMIT 8',(session,'user'))]
safe=[{k:r[k] for k in ('id','timestamp','role','content') if k in r} for r in rows]
(OUT/'RECENT_OWNER_USER_INSTRUCTIONS.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(snapshot=str(SNAP),manifest_files=len(receipt),live_match=sum(r['live_matches'] for r in receipt),dependencies=len(deps),recent_users=safe),ensure_ascii=False))
