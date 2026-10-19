"""Upload verified ZIP parts to a private GitHub Release without printing credentials."""
from pathlib import Path
import concurrent.futures,hashlib,http.client,json,subprocess,time,urllib.request,urllib.error,urllib.parse,datetime

P=Path('C:/Users/Admin/Documents/Codex/work/mf-portable-handoff-20261019')
A=P.parent/'mf-portable-assets-20261019'
REPO='anhduyhaha1234-droid/MotionForge2D-handoff-20261019'
TAG='v2026-10-19-portable'
BASE='https://api.github.com/repos/'+REPO
data=json.loads((P/'ASSET_RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
cred=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,timeout=20)
kv=dict(line.split('=',1) for line in cred.stdout.splitlines() if '=' in line)
TOKEN=kv.get('password','')
assert TOKEN,'GitHub credential unavailable'
HEAD=subprocess.check_output(['git','-C',str(P),'rev-parse','HEAD'],text=True).strip()
HEADERS={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','User-Agent':'MotionForge-portability','X-GitHub-Api-Version':'2022-11-28'}
def request(path,payload=None,method=None):
 headers=dict(HEADERS)
 if payload is not None:headers['Content-Type']='application/json';payload=json.dumps(payload).encode()
 req=urllib.request.Request(path,data=payload,headers=headers,method=method)
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
repo=request(BASE)
assert repo.get('private') is True,'Refuse to upload archive to a public repository'
try:release=request(BASE+'/releases/tags/'+TAG)
except urllib.error.HTTPError as ex:
 if ex.code!=404:raise
 release=request(BASE+'/releases',{'tag_name':TAG,'target_commitish':HEAD,'name':'MotionForge2D portable checkpoint 19-10-2026',
  'body':'Private source, prompt/rules, current RUN and project media backup. Verify every asset against ASSET_RELEASE_MANIFEST.json before restore. G1 candidate04 remains pending independent review.',
  'draft':False,'prerelease':False},method='POST')
assert release['tag_name']==TAG
print('RELEASE',release['html_url'],'release_id',release['id'],'parts',len(data['parts']),flush=True)
def list_assets():
 all=[];page=1
 while True:
  batch=request(BASE+f'/releases/{release["id"]}/assets?per_page=100&page={page}')
  all+=batch
  if len(batch)<100:return all
  page+=1
def existing(part):
 found=[a for a in list_assets() if a['name']==part['name'] and a.get('state')=='uploaded']
 if not found:return None
 a=found[0]
 if a['size']!=part['bytes']:raise RuntimeError('remote asset size mismatch: '+part['name'])
 digest=a.get('digest')
 if digest and digest!='sha256:'+part['sha256']:raise RuntimeError('remote digest mismatch: '+part['name'])
 return a
def upload(part):
 local=A/part['name']
 assert local.is_file() and local.stat().st_size==part['bytes']
 h=hashlib.sha256()
 with local.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 assert h.hexdigest()==part['sha256'],'local sha mismatch: '+part['name']
 already=existing(part)
 if already:return {'name':part['name'],'state':'already_uploaded','bytes':already['size'],'digest':already.get('digest'),'url':already['browser_download_url']}
 for attempt in range(1,4):
  conn=http.client.HTTPSConnection('uploads.github.com',timeout=900)
  try:
   path=f'/repos/{REPO}/releases/{release["id"]}/assets?'+urllib.parse.urlencode({'name':part['name']})
   conn.putrequest('POST',path)
   for k,v in {**HEADERS,'Content-Type':'application/zip','Content-Length':str(part['bytes'])}.items():conn.putheader(k,v)
   conn.endheaders()
   with local.open('rb') as f:
    for b in iter(lambda:f.read(4*1024*1024),b''):conn.send(b)
   resp=conn.getresponse();body=resp.read();status=resp.status
   if status==201:
    a=json.loads(body)
    if a.get('size')!=part['bytes']:raise RuntimeError('upload returned wrong size: '+part['name'])
    if a.get('digest') and a['digest']!='sha256:'+part['sha256']:raise RuntimeError('upload returned wrong digest: '+part['name'])
    return {'name':part['name'],'state':'uploaded','bytes':a['size'],'digest':a.get('digest'),'url':a['browser_download_url']}
   raise RuntimeError(f'HTTP {status} on {part["name"]}: '+body[:300].decode('utf-8','replace'))
  except Exception as ex:
   found=existing(part)
   if found:return {'name':part['name'],'state':'uploaded_after_connection_error','bytes':found['size'],'digest':found.get('digest'),'url':found['browser_download_url']}
   if attempt==3:raise
   print('RETRY',part['name'],'attempt',attempt,'reason',type(ex).__name__,flush=True)
   time.sleep(10*attempt)
  finally:conn.close()
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures={pool.submit(upload,part):part for part in data['parts']}
 for future in concurrent.futures.as_completed(futures):
  try:r=future.result()
  except Exception as ex:
   print('UPLOAD_FAILED',futures[future]['name'],type(ex).__name__,str(ex)[:300],flush=True)
   raise
  results.append(r)
  print('UPLOADED',r['name'],r['state'],r['bytes'],'digest',r.get('digest'),flush=True)
assert len(results)==len(data['parts'])
receipt={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo':REPO,'release':release['html_url'],
 'tag':TAG,'commit':HEAD,'assets':sorted(results,key=lambda x:x['name']),'all_size_verified':True,
 'all_remote_digest_verified':all(r.get('digest')=='sha256:'+next(p['sha256'] for p in data['parts'] if p['name']==r['name']) for r in results)}
(P/'GITHUB_RELEASE_UPLOAD_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE',len(results),'all_remote_digest_verified',receipt['all_remote_digest_verified'],flush=True)
