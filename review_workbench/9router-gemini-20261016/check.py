import argparse
import datetime as dt
import json
import sqlite3
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = 'http://127.0.0.1:20128'
DB = 'file:C:/Users/Admin/AppData/Roaming/9router/db/data.sqlite?mode=ro'

def api(path, payload=None, key=None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=55) as response:
            text = response.read().decode('utf-8')
            status = response.status
            if payload and payload.get('stream'):
                chunks = [json.loads(line[6:]) for line in text.splitlines() if line.startswith('data: ') and line[6:] != '[DONE]']
                result = {'model': next((c['model'] for c in chunks if c.get('model')), None),
                          'content': ''.join(x.get('delta', {}).get('content') or '' for c in chunks for x in c.get('choices', [])),
                          'done': 'data: [DONE]' in text,
                          'finish_reasons': [x['finish_reason'] for c in chunks for x in c.get('choices', []) if x.get('finish_reason')],
                          'usage': next((c['usage'] for c in reversed(chunks) if c.get('usage')), None)}
            else:
                result = json.loads(text)
    except urllib.error.HTTPError as e:
        status = e.code
        result = {'error': e.read(3000).decode('utf-8', errors='replace')}
    except (OSError, ValueError) as e:
        status = None
        result = {'error': str(e)}
    return {'status': status, 'seconds': round(time.monotonic() - start, 3), 'response': result}

def usage(after=0):
    with sqlite3.connect(DB, uri=True) as db:
        db.row_factory = sqlite3.Row
        return [dict(r) for r in db.execute('SELECT id,timestamp,provider,model,connectionId,status,promptTokens,completionTokens FROM usageHistory WHERE id>? AND provider=? ORDER BY id', (after, 'antigravity'))]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--mode', choices=['smoke', 'rotation'], default='smoke')
    args = p.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit('Refuse to overwrite receipt')
    keys = api('/api/keys')['response']['keys']
    key = next(k['key'] for k in keys if k.get('isActive'))
    connections = api('/api/providers')['response']['connections']
    accounts = [{'id': c['id'], 'active': c.get('isActive'), 'testStatus': c.get('testStatus')} for c in connections if c['provider'] == 'antigravity' and c.get('isActive')]
    initial = usage()
    latest = max((r['id'] for r in initial), default=0)
    result = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'mode': args.mode, 'accounts': accounts, 'tests': []}
    model = 'ag/gemini-3.8-flash-high'
    if args.mode == 'smoke':
        marker = 'STREAM_OK_' + uuid.uuid4().hex[:8]
        stream = api('/v1/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly ' + marker}], 'max_tokens': 128, 'stream': True, 'stream_options': {'include_usage': True}}, key)
        stream['pass'] = stream['status'] == 200 and stream['response'].get('content', '').strip() == marker and stream['response'].get('done') is True
        result['tests'].append({'test': 'stream_high', **stream})
        marker = 'TOOL_OK_' + uuid.uuid4().hex[:8]
        messages = [{'role': 'user', 'content': 'Call router_ping with token ' + marker + '. After receiving the result, reply with exactly its token.'}]
        tools = [{'type': 'function', 'function': {'name': 'router_ping', 'description': 'Returns the provided token unchanged.', 'parameters': {'type': 'object', 'properties': {'token': {'type': 'string'}}, 'required': ['token']}}}]
        body = {'model': model, 'messages': messages, 'tools': tools, 'tool_choice': {'type': 'function', 'function': {'name': 'router_ping'}}, 'max_tokens': 256, 'stream': False}
        call = api('/v1/chat/completions', body, key)
        message = (call['response'].get('choices') or [{}])[0].get('message', {})
        calls = message.get('tool_calls') or []
        valid = len(calls) == 1 and calls[0].get('function', {}).get('name') == 'router_ping'
        if valid:
            valid = json.loads(calls[0]['function']['arguments']).get('token') == marker
        call['pass'] = call['status'] == 200 and valid
        result['tests'].append({'test': 'tool_call', **call})
        if call['pass']:
            messages += [message, {'role': 'tool', 'tool_call_id': calls[0]['id'], 'content': json.dumps({'token': marker})}]
            body.update(messages=messages, tool_choice='none')
            reply = api('/v1/chat/completions', body, key)
            content = (reply['response'].get('choices') or [{}])[0].get('message', {}).get('content', '')
            reply['pass'] = reply['status'] == 200 and (content or '').strip() == marker
            result['tests'].append({'test': 'tool_result_roundtrip', **reply})
    else:
        if len(accounts) < 2:
            result['blocked'] = 'At least two active accounts required for live rotation proof'
        else:
            for i in range(len(accounts) + 1):
                reply = api('/v1/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly RR_OK'}], 'max_tokens': 64, 'stream': False}, key)
                content = (reply['response'].get('choices') or [{}])[0].get('message', {}).get('content', '')
                reply['pass'] = reply['status'] == 200 and (content or '').strip() == 'RR_OK'
                result['tests'].append({'test': 'rotation_' + str(i + 1), **reply})
                if not reply['pass']:
                    break
    time.sleep(2)
    result['usage_evidence'] = usage(latest)
    result['pass'] = bool(result['tests']) and all(t['pass'] for t in result['tests'])
    if args.mode == 'rotation':
        used = [r['connectionId'] for r in result['usage_evidence'] if r['model'].startswith('gemini-3.8-flash')]
        result['observed_connection_ids'] = used
        result['rotation_observed'] = len(set(used)) >= 2 and all(a != b for a, b in zip(used, used[1:]))
        result['pass'] = result['pass'] and result['rotation_observed']
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['pass'] else 1)

if __name__ == '__main__':
    main()
