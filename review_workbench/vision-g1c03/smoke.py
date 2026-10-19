import base64
import datetime as dt
import hashlib
import json
import secrets
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/motionforge-g1-review-03-20261019/vision'
OUT.mkdir(parents=True, exist_ok=True)
MODEL = 'ag/gemini-3.8-flash-high'
BASE = 'http://127.0.0.1:20128'
DB = 'file:C:/Users/Admin/AppData/Roaming/9router/db/data.sqlite?mode=ro'

def request(path, body=None, key=None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.read().decode(), round(time.monotonic()-started, 3)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace'), round(time.monotonic()-started, 3)

def usage(after=None):
    with sqlite3.connect(DB, uri=True) as db:
        db.row_factory = sqlite3.Row
        if after is None:
            return db.execute('SELECT COALESCE(MAX(id),0) FROM usageHistory').fetchone()[0]
        return [dict(r) for r in db.execute('SELECT id,timestamp,provider,model,substr(connectionId,1,8) AS connection_prefix,status,promptTokens,completionTokens FROM usageHistory WHERE id>? AND provider=? ORDER BY id',(after,'antigravity'))]

def run():
    receipt_path = OUT/'DIRECT_IMAGE_RECEIPT.json'
    if receipt_path.exists():
        raise SystemExit('Refusing repeated live test: receipt already exists')
    challenge = 'VIOLET-' + ''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))
    im = Image.new('RGB',(900,560),'white')
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',38)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    d.text((35,25),challenge,fill='black',font=f)
    d.polygon([(80,280),(150,130),(220,280)],fill='#e42727')
    d.ellipse((350,150,490,290),fill='#1565d8')
    for x in (600,690,780):
        d.rectangle((x,160,x+55,280),fill='#178844')
    d.text((65,320),'LEFT',fill='black',font=small)
    d.text((360,320),'CENTER',fill='black',font=small)
    d.text((650,320),'RIGHT',fill='black',font=small)
    d.text((35,430),'Check pixels, not filenames.',fill='black',font=small)
    image_path = OUT/'vision_fixture.png'
    im.save(image_path)
    data=image_path.read_bytes()
    prompt='Read only the attached image. Return JSON with code (exact top text), left_shape, left_color, center_shape, center_color, right_shape_count, right_color. If no pixels are visible say IMAGE_NOT_VISIBLE. Do not infer the code from context.'
    body={'model':MODEL,'messages':[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}}]}],'max_tokens':1024,'stream':False}
    status,raw,_=request('/api/keys')
    if status!=200:
        raise SystemExit('Local gateway key lookup unavailable; no live request made')
    key=next(k['key'] for k in json.loads(raw)['keys'] if k.get('isActive'))
    before=usage()
    status,raw,elapsed=request('/v1/chat/completions',body,key)
    # Never record auth headers or full request image data.
    parsed=json.loads(raw)
    content=(parsed.get('choices') or [{}])[0].get('message',{}).get('content','')
    candidate=content.strip()
    if candidate.startswith('```'):
        candidate=candidate.split('\n',1)[1].rsplit('```',1)[0].strip()
    try: answer=json.loads(candidate)
    except Exception: answer={}
    checks={'code_exact':answer.get('code')==challenge,'left_triangle':'triangle' in str(answer.get('left_shape','')).lower(),'left_red':'red' in str(answer.get('left_color','')).lower(),'center_circle':'circle' in str(answer.get('center_shape','')).lower(),'center_blue':'blue' in str(answer.get('center_color','')).lower(),'right_count':answer.get('right_shape_count')==3,'right_green':'green' in str(answer.get('right_color','')).lower()}
    receipt={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'purpose':'Single image smoke; no retries or manual account selection','endpoint':BASE+'/v1/chat/completions','requested_model':MODEL,'image':str(image_path),'image_sha256':hashlib.sha256(data).hexdigest(),'image_size':im.size,'image_bytes':len(data),'prompt':prompt,'expected':{'code':challenge,'left_shape':'triangle','left_color':'red','center_shape':'circle','center_color':'blue','right_shape_count':3,'right_color':'green'},'http_status':status,'seconds':elapsed,'raw_response_redacted':parsed,'checks':checks,'pass':status==200 and all(checks.values()),'usage_rows':usage(before),'request_count':1,'manual_account_override':False}
    receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['http_status','seconds','checks','pass','usage_rows']},indent=2))
    raise SystemExit(0 if receipt['pass'] else 1)

if __name__=='__main__': run()
