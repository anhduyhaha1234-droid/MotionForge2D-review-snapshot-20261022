from pathlib import Path
import datetime,hashlib,json
OUT=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=OUT/'c02b1-worker/candidate-01/MANIFEST.json'
manifest=json.loads(m.read_text());pre=json.loads((OUT/'C02B1_PREFLIGHT.json').read_text())
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'/root/motionforge_c02b1_coder','owner_tool_status':'completed','manifest_sha256':sha(m),'candidate_matches':all(sha(f[k]['path'])==f['live']['sha256'] for f in manifest['files'].values() for k in ('live','snapshot')),'protected_drift':[f['path'] for f in pre['files'] if f['role']=='protected' and sha(f['path'])!=f['sha256']],'evidence_drift':[f['path'] for f in manifest['evidence'] if sha(f['path'])!=f['sha256']],'root_results':{}}
for rel in ['root-review/c02b1-candidate-01/RESULT.json','root-review/C02B1_SCOPE_CANDIDATE01.json','root-review/c02b1-tests-candidate01/RESULT.json']:
    rec['root_results'][rel]={'sha256':sha(OUT/rel),'content':json.loads((OUT/rel).read_text())}
original=json.loads((OUT/'PREFLIGHT.json').read_text());rec['media_drift']=[label for label,f in original['media'].items() if sha(f['path'])!=f['sha256']]
rec['ok']=rec['candidate_matches'] and not any(rec[k] for k in ('protected_drift','evidence_drift','media_drift')) and rec['manifest_sha256']=='a03c3321b00a9ad29595e887946c4e054308fdea7c68c3368359c4288c9bd965'
p=OUT/'root-review/C02B1_RECONCILIATION_20261016T1917.json';assert not p.exists();p.write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps({'ok':rec['ok'],'candidate_matches':rec['candidate_matches'],'protected_drift':rec['protected_drift'],'evidence_drift':rec['evidence_drift'],'media_drift':rec['media_drift'],'receipt':str(p)}));assert rec['ok']

