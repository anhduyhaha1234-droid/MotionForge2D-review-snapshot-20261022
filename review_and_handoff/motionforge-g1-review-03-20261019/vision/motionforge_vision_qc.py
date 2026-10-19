"""Scoped Gemini image QC through the existing 9router route; no fallback/retry.

Receipts describe sampled images, never certify an entire video or Codex gate.
Uses only Python standard library. Credentials are resolved locally, never saved.
"""
from __future__ import annotations
import argparse,base64,datetime,hashlib,json,mimetypes,os,time,urllib.error,urllib.request
from pathlib import Path

MODEL='ag/gemini-3.8-flash-high'
BASE='http://127.0.0.1:20128'
DEFAULT_QUESTION='''Inspect the attached labeled frames against the supplied source and CAST references. Return JSON with observed, issues (frame_label, region, severity, defect, evidence, suggested_fix), uncertain, coverage, and overall_candidate (PASS/FAIL/UNKNOWN). Check identity, actor count, limbs, visibility/occlusion, hand-object contact, background/prop distortion, text, outlines and style. Do not infer unseen frames or audio, do not approve any project gate, and never claim temporal continuity from isolated images. Missing reference or coverage must remain UNKNOWN.'''

def http(path,body=None,key=None,timeout=120):
    headers={'Content-Type':'application/json'}
    if key:headers['Authorization']='Bearer '+key
    req=urllib.request.Request(BASE+path,headers=headers,data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.status,json.loads(r.read())

def resolve_key():
    key=os.environ.get('NINEROUTER_API_KEY','').strip()
    if key:return key
    _,d=http('/api/keys',timeout=5)
    # Same local gateway discovery as the verified smoke; never persist key.
    return next(k['key'] for k in d.get('keys',[]) if k.get('isActive'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',action='append',required=True,help='Local PNG/JPEG/WebP; repeat in source/reference/output order, at most8')
    p.add_argument('--label',action='append',help='Matching shot/frame/role/time label for each --image')
    p.add_argument('--question-file',type=Path,help='Optional exact QC question; UTF-8')
    p.add_argument('--out',type=Path,required=True,help='New unique receipt path; refuses overwrite')
    a=p.parse_args()
    if a.out.exists():p.error('Receipt exists. Preserve history; choose a new path.')
    if not 1<=len(a.image)<=8:p.error('Use1–8 images per call; split coverage into explicit batches.')
    labels=a.label or [f'frame_{i+1}' for i in range(len(a.image))]
    if len(labels)!=len(a.image):p.error('Exactly one label per image is required when labels are supplied.')
    question=a.question_file.read_text(encoding='utf-8-sig') if a.question_file else DEFAULT_QUESTION
    parts=[{'type':'text','text':question}];files=[];total=0
    for name,label in zip(a.image,labels):
        path=Path(name).resolve();data=path.read_bytes();total+=len(data)
        if path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):p.error('Only PNG/JPEG/WebP frames are accepted.')
        if total>12*1024*1024:p.error('Input images exceed12MB. Reduce the batch or image size explicitly.')
        mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        files.append({'path':str(path),'label':label,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        parts.extend([{'type':'text','text':'Frame label: '+label},{'type':'image_url','image_url':{'url':'data:'+mime+';base64,'+base64.b64encode(data).decode()}}])
    receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'endpoint':BASE+'/v1/chat/completions','requested_model':MODEL,'inputs':files,'question':question,'request_count':0,'fallback':False,'automatic_retry':False,'coverage':'Attached images only; no full-video/audio approval','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    start=time.monotonic();code=1
    try:
        key=resolve_key();receipt['request_count']=1
        status,result=http('/v1/chat/completions',{'model':MODEL,'messages':[{'role':'user','content':parts}],'max_tokens':2048,'stream':False},key)
        content=(result.get('choices') or [{}])[0].get('message',{}).get('content','')
        raw=content.strip()
        if raw.startswith('```'):raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
        try:parsed=json.loads(raw)
        except (ValueError,IndexError):parsed=None
        receipt.update(http_status=status,returned_model=result.get('model'),response_text=content,analysis_json=parsed,usage=result.get('usage'),transport_ok=status==200 and bool(content))
        code=0 if receipt['transport_ok'] else 1
    except urllib.error.HTTPError as e:
        receipt.update(http_status=e.code,transport_ok=False,error_type='HTTPError',action='Stop and inspect local router status; no automatic account/model switch.')
    except Exception as e:
        receipt.update(transport_ok=False,error_type=type(e).__name__,action='Keep this receipt. Diagnose before retry; timeout is not proof the server request was cancelled.')
    receipt['elapsed_seconds']=round(time.monotonic()-start,3)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(json.dumps({'receipt':str(a.out.resolve()),'transport_ok':receipt.get('transport_ok'),'http_status':receipt.get('http_status'),'error_type':receipt.get('error_type')},ensure_ascii=False))
    raise SystemExit(code)

if __name__=='__main__':main()
