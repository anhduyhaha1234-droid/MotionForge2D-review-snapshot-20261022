"""Package project media and run evidence into sub-2GiB portable ZIP parts."""
from pathlib import Path
import os,re,sys,json,zipfile,hashlib,datetime

P=Path('C:/Users/Admin/Documents/Codex/work/mf-portable-handoff-20261019')
A=P.parent/'mf-portable-assets-20261019'
ROOTS=[
 ('project_runtime/projects',Path('C:/Users/Admin/MotionForge2D/projects')),
 ('project_runtime/output',Path('C:/Users/Admin/MotionForge2D/output')),
 ('project_runtime/output_m05',Path('C:/Users/Admin/MotionForge2D/output_m05')),
 ('project_runtime/data',Path('C:/Users/Admin/MotionForge2D/data')),
 ('project_runtime/models_checkpoints',Path('C:/Users/Admin/MotionForge2D/models_checkpoints')),
 ('delivery_run',Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')),
]
NO_DIR={'.git','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.next','node_modules','venv','.venv','env','pylibs'}
NO_NAME={'.env','.env.local','auth.json','credentials.json'}
SECRET=re.compile(rb'(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{30,}|AIza[A-Za-z0-9_-]{25,}|Bearer [A-Za-z0-9._-]{30,})')
TEXT_EXT={'.py','.md','.json','.jsonl','.yaml','.yml','.toml','.txt','.tsx','.ts','.js','.jsx','.css','.html','.sh','.bat','.ps1','.ini','.sql','.csv','.log'}
MAX_PART=950_000_000
def sha_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def looks_secret(p):
 if p.suffix.lower() not in TEXT_EXT or p.stat().st_size>20_000_000:return False
 with p.open('rb') as f:return bool(SECRET.search(f.read()))
files=[];skipped=[];group_stats={}
for prefix,root in ROOTS:
 count=total=0
 for base,dirs,names in os.walk(root):
  dirs[:]=sorted(d for d in dirs if d not in NO_DIR)
  for name in sorted(names):
   src=Path(base)/name
   if name in NO_NAME or src.is_symlink():skipped.append({'path':str(src),'reason':'credential_or_symlink'});continue
   try:size=src.stat().st_size
   except OSError:skipped.append({'path':str(src),'reason':'stat_failed'});continue
   if looks_secret(src):skipped.append({'path':str(src),'reason':'secret_like_string'});continue
   files.append((src,prefix+'/'+src.relative_to(root).as_posix(),size));count+=1;total+=size
 group_stats[prefix]={'files':count,'bytes':total}
print(json.dumps({'groups':group_stats,'total_files':len(files),'total_GB':round(sum(x[2] for x in files)/1e9,3),'skipped_count':len(skipped),'skipped_reasons':{r:sum(x['reason']==r for x in skipped) for r in sorted({x['reason'] for x in skipped})}},indent=2),flush=True)
if '--plan' in sys.argv:sys.exit(0)
assert not A.exists(),'Refuse to overwrite prior archive output'
A.mkdir(parents=True)
parts=[];index=0;z=None;part_count=part_bytes=0
def close_part():
 global z,part_count,part_bytes
 if z is None:return
 z.close();p=A/f'motionforge-assets-{index:03d}.zip'
 parts.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha_file(p),'files':part_count,'uncompressed_bytes':part_bytes})
 print('PART_DONE',index,'files',part_count,'GB',round(p.stat().st_size/1e9,3),flush=True)
 z=None;part_count=part_bytes=0
for src,arc,size in files:
 if z is None or (part_count and part_bytes+size>MAX_PART):
  close_part();index+=1
  z=zipfile.ZipFile(A/f'motionforge-assets-{index:03d}.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True)
 try:z.write(src,arc)
 except OSError as ex:skipped.append({'path':str(src),'reason':'read_failed_'+type(ex).__name__});continue
 part_count+=1;part_bytes+=size
close_part()
manifest={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive_format':'zip-deflate-level1',
 'logical_roots':{k:str(v) for k,v in ROOTS},'parts':parts,'groups':group_stats,'skipped':skipped,
 'source_rule':'Historical project media and delivery run preserved. Reinstallable environments and credential files excluded.'}
(P/'ASSET_RELEASE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'parts':len(parts),'archive_GB':round(sum(p['bytes'] for p in parts)/1e9,3),'skipped':len(skipped),'manifest':str(P/'ASSET_RELEASE_MANIFEST.json')},indent=2),flush=True)
