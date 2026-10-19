"""Build an immutable, credential-free MotionForge2D source handoff tree."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, datetime, re

B=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
MAIN=Path('C:/Users/Admin/MotionForge2D')
P=Path('C:/Users/Admin/Documents/Codex/work/mf-portable-handoff-20261019')
EXCLUDE_TOP={'.git','.codex-review','data','diagnostics','models_checkpoints','output','output_m05','projects',
 'notepad-session-backup-20260910','notification-full-reset-20260912-021511','notification-full-reset-20260912-021526',
 'start-cache-backup-20260912-025407','windows-notification-db-backup-20260912-011517','wpn-inspect-20260914-144145'}
EXCLUDE_PARTS={'node_modules','.next','.venv','venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.git',
 '.DS_Store','.cache','cache'}
EXCLUDE_NAMES={'auth.json','config.yaml','.env','.env.local','debug.log','windows-notifications-backup-20260910.reg',
 'wpndatabase-inspect-20260912-012000.db','wpndatabase-inspect-20260912-012000.db-shm','wpndatabase-inspect-20260912-012000.db-wal'}
SECRET=re.compile(rb'(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{30,}|AIza[A-Za-z0-9_-]{25,}|Bearer [A-Za-z0-9._-]{30,})')
TEXT_EXT={'.py','.md','.json','.jsonl','.yaml','.yml','.toml','.txt','.tsx','.ts','.js','.jsx','.css','.html','.sh','.bat','.ps1','.ini','.sql','.csv'}
entries=[];skipped=[]
def sh(data):return hashlib.sha256(data).hexdigest()
def add(src,dst):
 if not src.is_file():return
 if dst.exists():
  if sh(dst.read_bytes())==sh(src.read_bytes()):return
  raise RuntimeError(f'destination exists with different bytes: {dst}')
 if src.name in EXCLUDE_NAMES or any(x in EXCLUDE_PARTS for x in src.parts):
  skipped.append({'source':str(src),'reason':'credential_or_generated_name'});return
 data=src.read_bytes()
 if src.suffix.lower() in TEXT_EXT and SECRET.search(data):
  skipped.append({'source':str(src),'reason':'secret_like_string'});return
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 entries.append({'path':dst.relative_to(P).as_posix(),'bytes':len(data),'sha256':sh(data),'source':str(src)})

assert not P.exists(),'Refuse to overwrite existing portable tree'
P.mkdir(parents=True)
proc=subprocess.run(['git','-C',str(MAIN),'ls-files','-z','--cached','--others','--exclude-standard'],capture_output=True,check=True)
for raw in proc.stdout.split(b'\0'):
 if not raw:continue
 rel=Path(os.fsdecode(raw));parts=rel.parts
 if not parts or parts[0] in EXCLUDE_TOP or any(x in EXCLUDE_PARTS for x in parts):continue
 add(MAIN/rel,P/'project'/rel)

for src_root,target in [(B/'outputs',P/'review_and_handoff'),(Path('C:/Users/Admin/.codex/skills'),P/'agent_rules/codex_skills'),
 (Path('C:/Users/Admin/.codex/rules'),P/'agent_rules/codex_rules'),
 (Path('C:/Users/Admin/AppData/Local/hermes/skills'),P/'agent_rules/hermes_skills'),
 (Path('C:/Users/Admin/AppData/Local/hermes/checkpoints'),P/'agent_rules/hermes_checkpoints')]:
 if not src_root.is_dir():continue
 for root,dirs,files in os.walk(src_root):
  dirs[:]=[d for d in dirs if d not in EXCLUDE_PARTS and not d.startswith('.git')]
  for name in files:
   src=Path(root)/name
   add(src,target/src.relative_to(src_root))
add(Path('C:/Users/Admin/AppData/Local/hermes/SOUL.md'),P/'agent_rules/HERMES_SOUL.md')
for src in (B/'work').glob('g1_*.py'):add(src,P/'review_tools'/src.name)
for src in (B/'work/g1-03-audit').glob('*.py'):add(src,P/'review_tools/g1-03-audit'/src.name)

manifest={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_git_head':subprocess.check_output(['git','-C',str(MAIN),'rev-parse','HEAD'],text=True).strip(),
 'source_git_remote':'https://github.com/anhduyhaha1234-droid/MotionForge2D.git','files':entries,'skipped':skipped}
(P/'PORTABLE_SOURCE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'tree':str(P),'files':len(entries),'bytes':sum(e['bytes'] for e in entries),'skipped':len(skipped),
 'skipped_by_reason':{r:sum(x['reason']==r for x in skipped) for r in sorted({x['reason'] for x in skipped})}},indent=2))
