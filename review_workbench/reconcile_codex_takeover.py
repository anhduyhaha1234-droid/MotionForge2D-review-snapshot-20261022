from pathlib import Path
import sys, json, hashlib, shutil, datetime
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/motionforge-codex-takeover-20261015'
RUN=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
sys.path.insert(0,str(RUN/'manager/tools'))
import invocation_runtime as rt
assert rt.run_root()==RUN.resolve()
snap=OUT/'preimages/ownership-reconciliation'
snap.mkdir(parents=True,exist_ok=True)
for p in list((RUN/'manager/leases').glob('*.json'))+[RUN/'manager/locks/controller.lock.meta.json']:
    if p.exists():
        d=snap/p.name
        if not d.exists(): shutil.copy2(p,d)
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authority':'user requests Codex takeover + gpt-6-sol max','ok':False,'old_invocation':'LONG01-R6g-20261014T0725Z-1572','helper_sha256':hashlib.sha256(Path(rt.__file__).read_bytes()).hexdigest(),'pre_controller':rt.controller_status()}
lock, meta=rt.acquire_controller_lock('codex-root-takeover-20261015',note='User-authorized terminal Hermes to Codex owner transfer; CPU C01 only',timeout=0)
rec['lock_acquire']=meta
try:
    if lock is None: raise RuntimeError('controller busy/unknown')
    lease=rt.read_json(RUN/'manager/leases/gpu_lease.LONG01-R6g-20261014T0725Z-1572.json')
    launcher=lease['launcher']
    rec['launcher_alive']=rt.identity_alive(launcher['pid'],launcher['created'],launcher['name'])
    if rec['launcher_alive'] is not False: raise RuntimeError('old launcher alive/unknown')
    rec['reconcile']=rt.reconcile_gpu_leases('codex-root-takeover-20261015')
    if rec['reconcile']['ok'] is not True: raise RuntimeError('lease reconciliation blocked')
    rec['post_active_leases']=rt.leases_status()
    rec['ok']=not rec['post_active_leases']
except Exception as e:
    rec['error']=str(e)
finally:
    if lock is not None: rt.release_controller_lock(lock,outcome='CODEX_TAKEOVER_PREFLIGHT_OK' if rec['ok'] else 'CODEX_TAKEOVER_BLOCKED')
    rec['post_controller']=rt.controller_status()
    (OUT/'OWNERSHIP_PREFLIGHT.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rec,ensure_ascii=False))
if not rec['ok']: raise SystemExit(2)
