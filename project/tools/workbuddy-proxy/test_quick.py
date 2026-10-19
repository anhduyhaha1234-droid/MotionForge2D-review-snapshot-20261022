import json, http.client
def chat(msg, model="hy4-preview"):
    conn=http.client.HTTPConnection('127.0.0.1',8787,timeout=30)
    conn.request('POST','/v1/chat/completions',json.dumps({'model':model,'messages':[{'role':'user','content':msg}]}),{'Content-Type':'application/json'})
    r=conn.getresponse()
    body=r.read().decode()
    j=json.loads(body)
    print(r.status, j['choices'][0]['message']['content'][:500])
    if 'reasoning_content' in j['choices'][0]['message']:
        print('reasoning:', j['choices'][0]['message']['reasoning_content'][:300])
    print('usage', j.get('usage'))
    return j

print("=== hy4-preview ===")
chat("say hello in one word")
print("\n=== hy4 alias ===")
chat("what is 2+2? answer in one short sentence", model="hy4")
print("\n=== models ===")
import urllib.request
print(urllib.request.urlopen("http://127.0.0.1:8787/v1/models", timeout=5).read().decode()[:500])
