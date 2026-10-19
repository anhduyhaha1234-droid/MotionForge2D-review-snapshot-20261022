from pathlib import Path
import ast, collections, datetime, hashlib, json, subprocess

OUT = Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015')
def sha(p):
    return hashlib.file_digest(Path(p).open('rb'), 'sha256').hexdigest()
pre = json.loads((OUT/'PREFLIGHT.json').read_text(encoding='utf-8'))
manifest_path = OUT/'c01-worker/candidate02/CANDIDATE_MANIFEST_R01.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'owner_status': 'completed; source/test writes stopped', 'manifest_sha256': sha(manifest_path), 'checked_preimages': len(pre['preimages']), 'changes': [], 'protected_media': [], 'candidate_files': [], 'git': [], 'duplicate_definitions': []}
expected_names = {'r6_gate.py', 'HERMES_AUTOPILOT_RULES.md', 'CODEX_PM_HANDOFF.md', 'ROADMAP.md'}
for name, before in pre['preimages'].items():
    p = Path(name)
    current = sha(p) if p.exists() else None
    if current != before['sha256']:
        rec['changes'].append({'path': name, 'expected_change': p.name in expected_names, 'pre_sha': before['sha256'], 'current_sha': current, 'bytes_before': before['bytes'], 'bytes_now': p.stat().st_size if p.exists() else None})
for label, before in pre['media'].items():
    current = sha(before['path'])
    rec['protected_media'].append({'label': label, 'sha256': current, 'unchanged': current == before['sha256']})
for f in manifest['files']:
    p = Path(f['path'])
    rec['candidate_files'].append({'role': f['role'], 'path': str(p), 'sha256': sha(p), 'matches': sha(p) == f['sha256']})
    if f['role'] in ('gate', 'test'):
        tree = ast.parse(p.read_text(encoding='utf-8'))
        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.Module, ast.ClassDef)):
                continue
            names = collections.Counter(n.name for n in parent.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
            for name, count in names.items():
                if count > 1:
                    rec['duplicate_definitions'].append({'path': str(p), 'name': name, 'count': count})
for repo in ('C:/Users/Admin/MotionForge2D', 'C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION'):
    entry = {'repo': repo}
    for key, args in [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--porcelain=v1'])]:
        r = subprocess.run(['git', '--no-optional-locks', '-C', repo, *args], capture_output=True, text=True, encoding='utf-8')
        entry[key] = {'rc': r.returncode, 'output': r.stdout.strip(), 'stderr': r.stderr}
    rec['git'].append(entry)
rec['unexpected_changes'] = [r for r in rec['changes'] if not r['expected_change']]
rec['ok'] = not rec['unexpected_changes'] and not rec['duplicate_definitions'] and all(f['matches'] for f in rec['candidate_files']) and all(f['unchanged'] for f in rec['protected_media'])
p = OUT/'root-review/PROTECTED_SCOPE_CHECK_02.json'
assert not p.exists()
p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': rec['ok'], 'preimages': rec['checked_preimages'], 'media': rec['protected_media'], 'unexpected_changes': rec['unexpected_changes'], 'duplicate_definitions': rec['duplicate_definitions'], 'heads': [r['head'] for r in rec['git']], 'receipt': str(p)}))
raise SystemExit(0 if rec['ok'] else 1)
