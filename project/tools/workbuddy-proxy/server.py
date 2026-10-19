#!/usr/bin/env python3
"""WorkBuddy HY4 local OpenAI-compatible proxy — stdlib only, no deps.
Reads live WorkBuddy auth from CodeBuddyExtension/Data/Public/auth,
forwards to https://www.workbuddy.ai/v2/chat/completions (hy4 model).
OpenAI compat: GET /v1/models, POST /v1/chat/completions (stream + non-stream), GET /health.
Usage: python server.py  [--port 8787] [--host 127.0.0.1]
Test: curl http://127.0.0.1:8787/v1/models
      curl http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"hy4-preview\",\"messages\":[{\"role\":\"user\",\"content\":\"say hi in one word\"}]}"
"""
import argparse, json, os, pathlib, sys, time, uuid, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def get_auth_path():
    if os.environ.get("WORKBUDDY_AUTH_FILE"):
        return os.environ["WORKBUDDY_AUTH_FILE"]
    base = os.environ.get("LOCALAPPDATA")
    if base: return str(pathlib.Path(base) / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
    up = os.environ.get("USERPROFILE")
    if up: return str(pathlib.Path(up) / "AppData" / "Local" / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
    return str(pathlib.Path.home() / "AppData" / "Local" / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
AUTH_PATH = get_auth_path()
UPSTREAM = "https://www.workbuddy.ai/v2/chat/completions"
MODELS = [
    {"id":"hy4-preview","object":"model","created":1787940000,"owned_by":"workbuddy"},
    {"id":"hy4","object":"model","created":1787940000,"owned_by":"workbuddy"},
    {"id":"hy3","object":"model","created":1787940000,"owned_by":"workbuddy"},
]

def get_auth():
    d=json.load(open(get_auth_path(),encoding="utf-8"))
    return d["auth"]["accessToken"], d["account"]["uid"]

def map_model(m):
    m=(m or "hy4-preview").lower()
    if m in ("hy4","hy4-preview","workbuddy/hy4-preview","workbuddy/hy4","hy4-preview-workbuddy"): return "hy4-preview"
    if m in ("hy3","workbuddy/hy3"): return "hy3"
    return m

def normalize_messages(msgs):
    out=[]
    for m in msgs or []:
        role=m.get("role","user")
        content=m.get("content")
        extras={k:m[k] for k in ("name","tool_call_id","tool_calls") if k in m}
        if content is None:
            out.append({"role":role,"content":[{"type":"text","text":""}],**extras})
            continue
        if isinstance(content,str):
            out.append({"role":role,"content":[{"type":"text","text":content}],**extras})
        elif isinstance(content,list):
            blocks=[]
            for p in content:
                if isinstance(p,dict) and p.get("type")=="text" and isinstance(p.get("text"),str):
                    blocks.append({"type":"text","text":p["text"]})
                elif isinstance(p,dict) and "text" in p and isinstance(p["text"],str):
                    blocks.append({"type":"text","text":p["text"]})
            if not blocks:
                blocks=[{"type":"text","text":str(content)}]
            out.append({"role":role,"content":blocks,**extras})
        else:
            out.append({"role":role,"content":[{"type":"text","text":str(content)}],**extras})
    if not any(m.get("role")=="system" for m in out):
        out.insert(0, {"role":"system","content":[{"type":"text","text":"You are a helpful AI assistant."}]})
    return out

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): sys.stderr.write(f"{self.client_address[0]} - - [{self.log_date_time_string()}] {fmt % a}\n")
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type, Authorization")
        self.end_headers()
    def do_GET(self):
        if self.path in ("/health","/v1/health"):
            self.json({"status":"ok","upstream":UPSTREAM,"auth_file":get_auth_path(),"models":[m["id"] for m in MODELS]})
        elif self.path in ("/v1/models","/v1/models/"):
            self.json({"object":"list","data":MODELS})
        elif self.path in ("/","/v1"):
            self.json({"ok":True,"endpoints":["GET /health","GET /v1/models","POST /v1/chat/completions"],"example":"curl http://127.0.0.1:8787/v1/chat/completions -H \"Content-Type: application/json\" -d '{\"model\":\"hy4-preview\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'"})
        else:
            self.send_error(404,f"not found: {self.path}")
    def do_POST(self):
        if self.path not in ("/v1/chat/completions","/v1/chat/completions/","/chat/completions","/v1/completions"):
            self.send_error(404,f"not found: {self.path}"); return
        length=int(self.headers.get("Content-Length") or 0)
        body=json.loads(self.rfile.read(length) or b"{}")
        # OpenAI -> upstream
        stream=bool(body.get("stream"))
        model=map_model(body.get("model") or "hy4-preview")
        messages=normalize_messages(body.get("messages") or [])
        # preserve temperature etc if provided
        upstream={
            "model": model,
            "messages": messages,
            "stream": True,  # upstream only supports stream
        }
        # reasoning: hy4 needs reasoning_effort high + summary auto to surface thinking (proven)
        eff=body.get("reasoning_effort") or body.get("reasoning") or None
        # also check extra body
        if isinstance(eff, dict): eff=eff.get("effort")
        if eff in ("none","off","disable"):
            pass  # omit
        elif eff:
            upstream["reasoning_effort"]=eff
            upstream["reasoning_summary"]="auto"
        elif model=="hy4-preview":
            upstream["reasoning_effort"]="high"
            upstream["reasoning_summary"]="auto"
        for k in ("temperature","top_p","max_tokens","max_completion_tokens","stop","frequency_penalty","presence_penalty"):
            if k in body and body[k] is not None:
                upstream[k]=body[k]
        for k in ("tools","tool_choice","parallel_tool_calls"):
            if k in body and body[k] is not None:
                upstream[k]=body[k]
        # streaming proxy
        try:
            token, uid = get_auth()
        except Exception as e:
            self.send_error(500,f"auth file read failed: {e} ({get_auth_path()})"); return
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-Id": uid,
            "Content-Type": "application/json",
            "User-Agent": "CLI/2.108.1 CodeBuddy/2.108.1",
            "X-Product": "SaaS",
            "X-IDE-Type": "CLI",
            "X-IDE-Name": "CLI",
            "x-requested-with": "XMLHttpRequest",
            "x-codebuddy-request": "1",
            "Accept": "text/event-stream",
        }
        data=json.dumps(upstream).encode()
        req=urllib.request.Request(UPSTREAM, data=data, headers=headers, method="POST")
        try:
            resp=urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            err=e.read().decode(errors="ignore")[:5000]
            # try to surface 401 refresh hint
            self.send_response(e.code)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"error":{"message":err,"type":"upstream_error","code":e.code}}).encode())
            return
        except Exception as e:
            self.send_error(502,f"upstream connect failed: {e}"); return

        if stream:
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
            self.send_header("Cache-Control","no-cache")
            self.send_header("Connection","keep-alive")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            # translate upstream SSE (chat.completion.chunk with delta.content + reasoning_content) -> OpenAI SSE
            # upstream already OpenAI-shaped, so we can passthrough with minimal rewrite, but ensure model id matches client
            cid=f"chatcmpl-{uuid.uuid4().hex[:24]}"
            created=int(time.time())
            # send role chunk first
            self.wfile.write(f"data: {json.dumps({'id':cid,'object':'chat.completion.chunk','created':created,'model':body.get('model') or model,'choices':[{'index':0,'delta':{'role':'assistant'},'finish_reason':None}]})}\n\n".encode())
            self.wfile.flush()
            buf=b""
            for chunk in resp:
                buf+=chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n",1)
                    line=line.strip()
                    if not line: continue
                    if line.startswith(b"data:"):
                        payload=line[5:].strip()
                        if payload==b"[DONE]":
                            self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
                            break
                        try:
                            j=json.loads(payload)
                        except: continue
                        # upstream j.choices[0].delta.{content, reasoning_content}
                        choice=(j.get("choices") or [{}])[0]
                        delta=choice.get("delta") or {}
                        out_delta={}
                        if delta.get("content"): out_delta["content"]=delta["content"]
                        # map reasoning_content -> reasoning_content (many clients read it) but also expose as delta.reasoning_content
                        if delta.get("reasoning_content"): out_delta["reasoning_content"]=delta["reasoning_content"]
                        # also handle tool_calls passthrough
                        if delta.get("tool_calls"): out_delta["tool_calls"]=delta["tool_calls"]
                        if not out_delta and delta.get("role"): continue  # already sent
                        if not out_delta: continue
                        fr=choice.get("finish_reason")
                        out=json.dumps({"id":cid,"object":"chat.completion.chunk","created":created,"model":body.get("model") or model,"choices":[{"index":0,"delta":out_delta,"finish_reason":fr}]})
                        self.wfile.write(f"data: {out}\n\n".encode()); self.wfile.flush()
                        if fr: pass
                    # else ignore
                # need to check for DONE inside loop? outer will continue reading
            # ensure DONE
            try: self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
            except: pass
        else:
            # non-stream: collect all
            content_parts=[]; reasoning_parts=[]; tool_calls=[]; finish="stop"; usage=None; mid=None
            buf=b""
            for chunk in resp:
                buf+=chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n",1)
                    line=line.strip()
                    if not line: continue
                    if line.startswith(b"data:"):
                        payload=line[5:].strip()
                        if payload==b"[DONE]": break
                        try: j=json.loads(payload)
                        except: continue
                        mid=j.get("id") or mid
                        choice=(j.get("choices") or [{}])[0]
                        delta=choice.get("delta") or {}
                        if delta.get("content"): content_parts.append(delta["content"])
                        if delta.get("reasoning_content"): reasoning_parts.append(delta["reasoning_content"])
                        if delta.get("tool_calls"): tool_calls.extend(delta["tool_calls"])
                        if choice.get("finish_reason"): finish=choice.get("finish_reason") or finish
                        if j.get("usage"): usage=j["usage"]
            text="".join(content_parts)
            reasoning="".join(reasoning_parts)
            out={
                "id": mid or f"chatcmpl-{uuid.uuid4().hex[:24]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model") or model,
                "choices": [{"index":0,"message":{"role":"assistant","content":text},"finish_reason":finish}],
                "usage": usage or {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},
            }
            if reasoning:
                out["choices"][0]["message"]["reasoning_content"]=reasoning
                out["choices"][0]["message"]["reasoning"]=reasoning
            if tool_calls:
                out["choices"][0]["message"]["tool_calls"]=tool_calls
            self.json(out)

    def json(self, obj, code=200):
        data=json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(data)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=8787)
    ap.add_argument("--host",default="127.0.0.1")
    args=ap.parse_args()
    srv=ThreadingHTTPServer((args.host,args.port), Handler)
    print(f"WorkBuddy HY4 OpenAI proxy listening on http://{args.host}:{args.port}")
    print(f"  auth: {get_auth_path()}")
    print(f"  upstream: {UPSTREAM}")
    print(f"  models: {', '.join(m['id'] for m in MODELS)} (all map to hy4-preview upstream)")
    print(f"  test: curl http://{args.host}:{args.port}/v1/models")
    print(f"        curl http://{args.host}:{args.port}/v1/chat/completions -H \"Content-Type: application/json\" -d '{{\"model\":\"hy4-preview\",\"messages\":[{{\"role\":\"user\",\"content\":\"say hi\"}}]}}'")
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nbye")
