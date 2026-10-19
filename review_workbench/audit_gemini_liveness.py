from pathlib import Path
import sqlite3, json, re, hashlib, datetime, sys

sys.stdout.reconfigure(encoding='utf-8')
base=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
out=base/'outputs/motionforge-gemini-independent-audit-20261017'
ex=base/'outputs/motionforge-gemini-handoff-20261017/execution'
out.mkdir(parents=True,exist_ok=True)
sid='20261017_115944_b2a338'
tz=datetime.timezone(datetime.timedelta(hours=7))

def redact(s):
    s=re.sub(r'\b\d{7,13}:[A-Za-z0-9_-]{25,}\b','[BOT_TOKEN_REDACTED]',s or '')
    s=re.sub(r'\b(?:sk-|sk_)[A-Za-z0-9_-]{12,}\b','[KEY_REDACTED]',s)
    s=re.sub(r'(?i)(Bearer\s+)\S+',r'\1[REDACTED]',s)
    s=re.sub(r'(?im)^.*(?:TOKEN\s*=|CHAT_ID\s*=).*$', '[CREDENTIAL_OR_RECIPIENT_LINE_REDACTED]',s)
    return s

def db(path):
    c=sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True)
    c.row_factory=sqlite3.Row
    c.execute('pragma query_only=on')
    return c

def save(name,data):
    (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def file_info(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mtime_local':datetime.datetime.fromtimestamp(p.stat().st_mtime,tz).isoformat()}

router=db('C:/Users/Admin/AppData/Roaming/9router/db/data.sqlite')
usage=[dict(r) for r in router.execute("select id,timestamp,provider,model,status,promptTokens,completionTokens from usageHistory where model like '%gemini%' and timestamp >= '2026-10-17T08:50:00' order by id")]
left=next(r for r in usage if r['id']==63324)
right=next(r for r in usage if r['id']==63325)
dt=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
gap={'last_before':left,'first_after':right,'seconds':(dt(right['timestamp'])-dt(left['timestamp'])).total_seconds(),'last_before_local':dt(left['timestamp']).astimezone(tz).isoformat(),'first_after_local':dt(right['timestamp']).astimezone(tz).isoformat(),'all_router_usage_rows_strictly_between':router.execute('select count(*) from usageHistory where timestamp>? and timestamp<?',(left['timestamp'],right['timestamp'])).fetchone()[0]}
save('ROUTER_USAGE.json',{'observed_at':datetime.datetime.now(tz).isoformat(),'gap':gap,'recent_rows':usage})
router.close()

c=db('C:/Users/Admin/AppData/Local/hermes/state.db')
messages=[dict(r) for r in c.execute('select id,role,timestamp,content,tool_calls,tool_name,finish_reason from messages where session_id=? order by id',(sid,))]
historical_tests=[]
heartbeat_versions=[]
for m in messages:
    if m['role']=='tool' and m['tool_name']=='terminal':
        try: content=json.loads(m['content'])
        except (ValueError,TypeError): continue
        text=content.get('output','')
        if re.search(r'Ran (?:54|64) tests',text) and content.get('exit_code')==0:
            historical_tests.append({'message_id':m['id'],'timestamp_local':datetime.datetime.fromtimestamp(m['timestamp'],tz).isoformat(),'exit_code':content['exit_code'],'output':redact(text),'note':'Historical tool output, not fresh root test execution'})
    if m['tool_calls']:
        try: calls=json.loads(m['tool_calls'])
        except (ValueError,TypeError):continue
        for call in calls:
            f=call.get('function',{})
            if f.get('name')!='write_file':continue
            try: args=json.loads(f.get('arguments','{}'))
            except (ValueError,TypeError):continue
            path=args.get('path','') or args.get('file_path','')
            if str(path).endswith('telegram_heartbeat.py'):
                text=redact(args.get('content',''))
                name=f"heartbeat_message_{m['id']}_redacted.txt"
                (out/name).write_text(text,encoding='utf-8')
                heartbeat_versions.append({'message_id':m['id'],'timestamp_local':datetime.datetime.fromtimestamp(m['timestamp'],tz).isoformat(),'snapshot':name,'original_path':path})
save('HISTORICAL_TEST_OUTPUTS.json',historical_tests)
focus=[]
for m in messages:
    if m['id'] in (295581,295728,295729) or (m['role']=='assistant' and m['timestamp']>=1792254291 and m['finish_reason']=='stop'):
        focus.append({'message_id':m['id'],'role':m['role'],'timestamp_local':datetime.datetime.fromtimestamp(m['timestamp'],tz).isoformat(),'finish_reason':m['finish_reason'],'content':redact(m['content'])})
save('SESSION_EVIDENCE.json',{'session_id':sid,'heartbeat_user_authorized_at':'2026-10-17T13:26:07+07:00','messages':focus,'heartbeat_versions':heartbeat_versions,'recent_message_index':[{'id':m['id'],'role':m['role'],'tool_name':m['tool_name'],'finish_reason':m['finish_reason'],'time_local':datetime.datetime.fromtimestamp(m['timestamp'],tz).isoformat()} for m in messages[-25:]]})
c.close()

for name in ['STATE.json','CHECKPOINT.json']:
    data=json.loads((ex/name).read_text(encoding='utf-8-sig'))
    save('SNAPSHOT_'+name,data)

cp=json.loads((ex/'CHECKPOINT.json').read_text(encoding='utf-8-sig'))
cpcheck=[]
for f in cp['files']:
    info=file_info(Path(f['live_path']));info['recorded_sha256']=f['sha256'];info['matches']=info['sha256']==f['sha256'];cpcheck.append(info)
latest=[]
r6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6')
for folder in [r6/'scripts',r6/'tests']:
    latest.extend(file_info(p) for p in folder.glob('*.py'))
latest.sort(key=lambda x:x['mtime_local'],reverse=True)
heartbeat=ex/'telegram_heartbeat.py'
(out/'HEARTBEAT_CURRENT_REDACTED.txt').write_text(redact(heartbeat.read_text(encoding='utf-8')),encoding='utf-8')
save('FILES_EVIDENCE.json',{'observed_at':datetime.datetime.now(tz).isoformat(),'state':file_info(ex/'STATE.json'),'checkpoint':file_info(ex/'CHECKPOINT.json'),'checkpoint_hash_checks':cpcheck,'latest_source_and_tests':latest[:10],'a3_directory_exists':(ex/'A3').exists(),'heartbeat':file_info(heartbeat),'heartbeat_log':file_info(ex/'telegram_heartbeat.log')})
print(json.dumps({'out':str(out),'gap_seconds':gap['seconds'],'usage_in_gap':gap['all_router_usage_rows_strictly_between'],'historical_passing_test_outputs':len(historical_tests),'heartbeat_versions':heartbeat_versions,'checkpoint_matches':sum(x['matches'] for x in cpcheck),'a3_exists':(ex/'A3').exists()},ensure_ascii=False))
