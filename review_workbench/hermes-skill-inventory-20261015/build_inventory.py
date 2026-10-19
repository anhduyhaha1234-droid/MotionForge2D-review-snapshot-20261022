from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/Users/Admin/AppData/Local/hermes/skills')
BUNDLES = Path('C:/Users/Admin/AppData/Local/hermes/skill-bundles')
OUT = Path(__file__).resolve().parent
MATCH = re.compile(r'motionforge|comfyui|WanAnimate|identity5m|SAM2|CoTracker|VACE|MF-DEMO-LONG', re.I)
SUPPORT = {
    'bom-context-budget-manager', 'bom-session-checkpoint-handoff',
    'bom-quota-budget-planner', 'bom-retry-rate-limit-controller',
    'bom-tool-output-minimizer', 'bom-usage-audit', 'bom-model-routing',
    'bom-cache-friendly-prompting', 'bom-batch-deduplicate', 'bom-skill-index-hygiene',
    'bom-repository-inspection', 'bom-requirements-to-plan', 'bom-verified-implementation',
    'bom-systematic-debugging', 'terminal-engineering-discipline', 'plan',
    'test-driven-development', 'systematic-debugging', 'requesting-code-review',
}
FULLY_READ = {
    'motionforge-autopilot', 'comfyui-video-model-proof', 'local-comfyui-adapter-proof',
    'subagent-orchestration', 'worktree-integration-audit', 'plan', 'requesting-code-review',
    'bom-context-budget-manager', 'bom-session-checkpoint-handoff',
    'bom-quota-budget-planner', 'bom-retry-rate-limit-controller', 'bom-tool-output-minimizer',
    'bom-usage-audit', 'bom-model-routing', 'bom-cache-friendly-prompting',
    'bom-batch-deduplicate', 'bom-skill-index-hygiene', 'bom-repository-inspection',
    'bom-requirements-to-plan', 'bom-verified-implementation', 'bom-systematic-debugging',
}
PARTIAL = {
    'motionforge-2d-project': 'Lines 1-193 (architecture, conventions, source authority, validation, liveness); full heading index. Remaining history/patterns not semantically loaded.',
    'motionforge-sprint-manager': 'Lines 1-103; referenced long-scope-manager-dispatch-20261005.md read in full. Remaining historical cases indexed, not semantically loaded.',
    'terminal-engineering-discipline': 'First 22 rules and later portions in truncated initial read; not a full semantic read. Unsafe authority-overriding text flagged.',
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def row_for_file(path: Path) -> dict:
    data = path.read_bytes()
    return {
        'source': str(path).replace('\\', '/'),
        'relative_path': path.relative_to(ROOT).as_posix(),
        'bytes': len(data), 'sha256': sha(data),
        'mtime_ns': path.stat().st_mtime_ns,
        'symlink': path.is_symlink(),
    }

paths = sorted(Path(p) for p in subprocess.check_output(
    ['rg', '--files', str(ROOT), '-g', 'SKILL.md'], text=True, encoding='utf-8').splitlines())
all_skills = []
selected = []
all_names = set()
for path in paths:
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig', errors='replace')
    name_match = re.search(r'^name:\s*(.+?)\s*$', text, re.M)
    description_match = re.search(r'^description:\s*(.+?)\s*$', text, re.M)
    name = (name_match.group(1).strip('"\'') if name_match else path.parent.name)
    all_names.add(name)
    direct = bool(MATCH.search(text))
    relevant = direct or name in SUPPORT
    row = row_for_file(path)
    row.update({
        'name': name,
        'description': description_match.group(1).strip('"\'') if description_match else None,
        'line_count': len(text.splitlines()),
        'selection': 'direct_project_or_video_mention' if direct else ('essential_support' if relevant else 'not_selected'),
        'read_coverage': 'full' if name in FULLY_READ else ('partial' if name in PARTIAL else 'inventory_only'),
        'read_detail': PARTIAL.get(name),
        'heading_index': [{'line': i, 'heading': line} for i, line in enumerate(text.splitlines(), 1) if re.match(r'^#{1,4}\s', line)],
        'tool_portability': 'Requires Codex tool mapping and authority overlay; not executed.',
    })
    all_skills.append(row)
    if relevant:
        entries = [row_for_file(file) for file in sorted(path.parent.rglob('*')) if file.is_file()]
        selected.append({
            'name': name, 'source_directory': str(path.parent).replace('\\', '/'),
            'relative_directory': path.parent.relative_to(ROOT).as_posix(),
            'skill_md_sha256': sha(raw), 'selection': row['selection'],
            'read_coverage': row['read_coverage'], 'files': entries,
            'file_count': len(entries), 'total_bytes': sum(e['bytes'] for e in entries),
        })

bundle_rows = []
for path in sorted(BUNDLES.glob('*.yaml')):
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    names = re.findall(r'^\s+-\s+(\S+)\s*$', text, re.M)
    bundle_rows.append({'source': str(path).replace('\\', '/'), 'bytes': len(data), 'sha256': sha(data),
                        'referenced_skills': names, 'missing_skill_names': [n for n in names if n not in all_names]})

manifest = {
    'schema_version': 1, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_root': str(ROOT).replace('\\', '/'),
    'scope': 'Read-only inventory. No tools/scripts/hooks executed; no global install; no runtime/registry/config/credentials read or changed.',
    'interpretation': 'Library availability, semantic loading, tool runnable status, inference proof, and product acceptance are separate facts.',
    'counts': {'all_skill_md': len(all_skills), 'direct_project_video_skills': sum(s['selection'] == 'direct_project_or_video_mention' for s in all_skills),
               'selected_skills': len(selected), 'selected_directory_files': sum(s['file_count'] for s in selected),
               'selected_directory_bytes': sum(s['total_bytes'] for s in selected),
               'fully_read_skills': len(FULLY_READ), 'partially_read_skills': len(PARTIAL),
               'bundle_yaml_files': len(bundle_rows)},
    'all_skills': all_skills, 'selected_skill_directories': selected, 'bundles': bundle_rows,
}
(OUT / 'HERMES_SKILL_INVENTORY.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'SELECTED_SKILL_NAMES.txt').write_text('\n'.join(s['relative_directory'] for s in selected) + '\n', encoding='utf-8')
print(json.dumps({'counts': manifest['counts'], 'missing_bundle_dependencies': {Path(b['source']).name: b['missing_skill_names'] for b in bundle_rows if b['missing_skill_names']}, 'manifest': str(OUT / 'HERMES_SKILL_INVENTORY.json')}, ensure_ascii=False, indent=2))
