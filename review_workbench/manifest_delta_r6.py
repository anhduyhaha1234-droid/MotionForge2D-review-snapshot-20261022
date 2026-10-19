from pathlib import Path
import json,hashlib
O=Path(r'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014')
m=json.loads((O/'PACKET_MANIFEST.json').read_text(encoding='utf-8'))
out=[]
for old in m['files']:
    p=O/old['path'];b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
    if h!=old['sha256']:out.append({'old':old,'new':{'path':old['path'],'bytes':len(b),'sha256':h}})
print(json.dumps(out))
