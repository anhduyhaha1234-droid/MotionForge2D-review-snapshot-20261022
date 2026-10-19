#!/usr/bin/env python3
"""WorkBuddy HY4 OpenAI-compatible proxy — stdlib only, no deps.
Reads live auth file each request, forwards to https://www.workbuddy.ai/v2/chat/completions,
Translates OpenAI <-> WorkBuddy shapes, supports stream + non-stream.
ponytail: minimal mapping; upgrade to full tool_calls/function when upstream adds it.
"""
import json, os, pathlib, time, uuid, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def _default_auth_path():
    base = os.environ.get("LOCALAPPDATA")
    if base: return str(pathlib.Path(base) / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
    up = os.environ.get("USERPROFILE")
    if up: return str(pathlib.Path(up) / "AppData" / "Local" / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
    return str(pathlib.Path.home() / "AppData" / "Local" / "CodeBuddyExtension" / "Data" / "Public" / "auth" / "workbuddy-desktop-ai.info")
AUTH_FILE = os.environ.get("WORKBUDDY_AUTH_FILE", _default_auth_path())
UPSTREAM = os.environ.get("WORKBUDDY_UPSTREAM", "https://www.workbuddy.ai/v2/chat/completions")
REFRESH_URL = os.environ.get("WORKBUDDY_REFRESH_URL", "https://www.workbuddy.ai/v2/plugin/auth/token/refresh")
PORT = int(os.environ.get("PORT", "8787"))

MODEL_MAP = {
    "hy4-preview": "hy4-preview", "hy4": "hy4-preview", "workbuddy/hy4-preview": "hy4-preview",
    "hy3": "hy3", "hy3-preview": "hy3", "workbuddy/hy3": "hy3",
}
AVAILABLE_MODELS = ["hy4-preview", "hy4", "hy3"]

def load_auth():
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    tok = d.get("auth", {}).get("accessToken", "")
    refresh = d.get("auth", {}).get("refreshToken", "")
    uid = d.get("account", {}).get("uid", "") or d.get("auth", {}).get("uid", "")
    # fallback: try allAccounts
    if not uid and d.get("allAccounts"):
        uid = d["allAccounts"][0].get("uid","")
    return tok, refresh, uid, d

def save_auth(new_auth_dict):
    # preserve file shape; update auth.accessToken etc from response if possible
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            cur = json.load(f)
    except: cur = {}
    cur["auth"].update(new_auth_dict)
    tmp = AUTH_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    os.replace(tmp, AUTH_FILE)

def try_refresh(refresh_token):
    if not refresh_token: return None
    body = json.dumps({}).encode()
    # upstream expects X-Refresh-Token header; method POST json
    headers = {
        "Content-Type": "application/json",
        "X-Refresh-Token": refresh_token,
        "X-Auth-Refresh-Source": "plugin",
        "User-Agent": "CLI/2.108.1 CodeBuddy/2.108.1",
        "X-Product": "SaaS",
        "X-IDE-Type": "CLI",
        "X-IDE-Name": "CLI",
        "x-requested-with": "XMLHttpRequest",
        "x-codebuddy-request": "1",
    }
    req = urllib.request.Request(REFRESH_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            j = json.loads(r.read().decode())
            # response shape unknown — try common keys
            data = j.get("data") or j
            at = data.get("accessToken") or data.get("access_token") or data.get("token")
            rt = data.get("refreshToken") or data.get("refresh_token")
            upd = {}
            if at: upd["accessToken"] = at
            if rt: upd["refreshToken"] = rt
            if "expiresIn" in data: upd["expiresIn"] = data["expiresIn"]
            if upd: save_auth(upd)
            return upd.get("accessToken")
    except Exception as e:
        print(f"[refresh] failed: {e}")
    return None

def normalize_messages(msgs):
    """OpenAI messages -> upstream typed blocks. System stays system."""
    out = []
    for m in msgs:
        role = m.get("role","user")
        content = m.get("content","")
        if isinstance(content, list):
            # already typed blocks? preserve text parts
            blocks = []
            for b in content:
                if isinstance(b, dict) and b.get("type")=="text":
                    blocks.append({"type":"text","text": b.get("text","")})
                elif isinstance(b, dict) and "text" in b:
                    blocks.append({"type":"text","text": b["text"]})
                else:
                    blocks.append({"type":"text","text": str(b)})
            # for system, upstream expects string content, not blocks — keep string
            if role == "system":
                out.append({"role": role, "content": " ".join(x["text"] for x in blocks)})
            else:
                out.append({"role": role, "content": blocks})
        elif isinstance(content, str):
            if role == "system":
                out.append({"role": role, "content": content})
            else:
                out.append({"role": role, "content": [{"type":"text","text": content}]})
        else:
            out.append({"role": role, "content": [{"type":"text","text": str(content)}]})
    # ensure first system is preserved; upstream wants system first
    return out

def upstream_headers(token, uid):
    return {
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

def call_upstream(messages, model_upstream):
    token, refresh, uid, _raw = load_auth()
    if not token or not uid:
        raise RuntimeError(f"auth file missing token/uid ({AUTH_FILE})")
    payload = {
        "model": model_upstream,
        "messages": messages,
        "stream": True,
        "reasoning_effort": "high",
        "reasoning_summary": "auto",
    }
    body = json.dumps(payload).encode()
    headers = upstream_headers(token, uid)
    req = urllib.request.Request(UPSTREAM, data=body, headers=headers, method="POST")
    try:
        return urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        if e.code == 401 and refresh:
            nt = try_refresh(refresh)
            if nt:
                headers["Authorization"] = f"Bearer {nt}"
                req2 = urllib.request.Request(UPSTREAM, data=body, headers=headers, method="POST")
                return urllib.request.urlopen(req2, timeout=120)
        # re-raise with body
        body_txt = ""
        try: body_txt = e.read().decode(errors="ignore")[:3000]
        except: pass
        raise RuntimeError(f"upstream HTTP {e.code}: {body_txt}") from e

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # quiet except errors
        if "404" in fmt % args or "500" in fmt % args:
            super().log_message(fmt, *args)

    def send_json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","*")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            # also verify auth file readable
            try:
                tok, _, uid, _ = load_auth()
                ok = bool(tok and uid)
            except Exception as e:
                self.send_json(500, {"status":"error","error":str(e)}); return
            self.send_json(200, {"status":"ok","auth_loaded": ok, "upstream": UPSTREAM})
            return
        if self.path.startswith("/v1/models"):
            now = int(time.time())
            data = [{"id": m, "object":"model","created": now, "owned_by":"workbuddy"} for m in AVAILABLE_MODELS]
            self.send_json(200, {"object":"list","data": data})
            return
        self.send_json(404, {"error":{"message":"not found","type":"invalid_request_error"}})

    def do_POST(self):
        if self.path.startswith("/v1/chat/completions"):
            length = int(self.headers.get("Content-Length","0"))
            raw = self.rfile.read(length) if length else b"{}"
            try: body=json.loads(raw.decode() or "{}")
            except: self.send_json(400, {"error":{"message":"invalid json"}}); return
            self.handle_chat(body)
            return
        if self.path.startswith("/v1/completions"):
            length = int(self.headers.get("Content-Length","0"))
            raw = self.rfile.read(length) if length else b"{}"
            try: body=json.loads(raw.decode() or "{}")
            except: self.send_json(400, {"error":{"message":"invalid json"}}); return
            prompt = body.get("prompt","")
            if isinstance(prompt, list): prompt = "\n".join(str(x) for x in prompt)
            model = body.get("model","hy4-preview")
            stream = bool(body.get("stream", False))
            chat_body = {"model": model, "messages":[{"role":"user","content": prompt}], "stream": stream}
            self.handle_chat(chat_body)
            return
        self.send_json(404, {"error":{"message":"not found"}})

    def handle_chat(self, body):

        req_model = body.get("model","hy4-preview")
        model_up = MODEL_MAP.get(req_model, "hy4-preview")
        is_stream = bool(body.get("stream", False))
        # also honor stream via Accept? no — explicit only

        msgs_in = body.get("messages", [])
        if not msgs_in:
            self.send_json(400, {"error":{"message":"messages required"}}); return
        # if system not present, inject default so upstream behaves as CodeBuddy
        has_system = any(m.get("role")=="system" for m in msgs_in)
        if not has_system:
            msgs_in = [{"role":"system","content":"You are CodeBuddy Code."}] + msgs_in

        upstream_msgs = normalize_messages(msgs_in)

        # call upstream (always stream=true)
        try:
            resp = call_upstream(upstream_msgs, model_up)
        except Exception as e:
            self.send_json(502, {"error":{"message": str(e), "type":"upstream_error"}}); return

        # helper to parse SSE lines
        def iter_upstream_chunks(http_resp):
            for raw_line in http_resp:
                try: line = raw_line.decode(errors="ignore")
                except: continue
                line=line.strip()
                if not line: continue
                if not line.startswith("data:"): continue
                data = line[5:].strip()
                if data == "[DONE]": break
                try: j=json.loads(data)
                except: continue
                yield j

        if is_stream:
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
            self.send_header("Cache-Control","no-cache")
            self.send_header("Connection","keep-alive")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("X-Accel-Buffering","no")
            self.end_headers()
            created = int(time.time())
            cid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            # first chunk with role
            first = {"id": cid, "object":"chat.completion.chunk","created": created, "model": req_model,
                     "choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":None}]}
            try:
                self.wfile.write(f"data: {json.dumps(first, ensure_ascii=False)}\n\n".encode())
            except: return
            finish_reason = None
            usage = None
            try:
                for j in iter_upstream_chunks(resp):
                    choices = j.get("choices") or []
                    if not choices: continue
                    c = choices[0]
                    delta = c.get("delta") or {}
                    fr = c.get("finish_reason")
                    if c.get("usage"): usage = c["usage"]
                    if j.get("usage"): usage = j["usage"]
                    if fr: finish_reason = fr
                    out_delta = {}
                    if delta.get("content"):
                        out_delta["content"] = delta["content"]
                    if delta.get("reasoning_content"):
                        # OpenAI compat: reasoning_content (used by many clients)
                        out_delta["reasoning_content"] = delta["reasoning_content"]
                        # also expose as reasoning for newer spec
                        out_delta["reasoning"] = delta["reasoning_content"]
                    if not out_delta and not fr:
                        continue
                    chunk = {"id": cid, "object":"chat.completion.chunk","created": created, "model": req_model,
                             "choices":[{"index":0,"delta": out_delta, "finish_reason": fr or None}]}
                    if fr and usage:
                        chunk["usage"] = usage
                    try:
                        self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode())
                        self.wfile.flush()
                    except:
                        break
                    if fr:
                        break
                # final stop chunk if not already sent
                if not finish_reason:
                    finish_reason = "stop"
                end = {"id": cid, "object":"chat.completion.chunk","created": created, "model": req_model,
                       "choices":[{"index":0,"delta":{},"finish_reason": finish_reason}]}
                if usage: end["usage"]=usage
                try: self.wfile.write(f"data: {json.dumps(end, ensure_ascii=False)}\n\n".encode())
                except: pass
                try: self.wfile.write(b"data: [DONE]\n\n")
                except: pass
            finally:
                try: resp.close()
                except: pass
            return
        else:
            # non-stream: collect
            content_parts=[]; reasoning_parts=[]; finish_reason=None; usage=None; upstream_id=None
            try:
                for j in iter_upstream_chunks(resp):
                    if not upstream_id: upstream_id = j.get("id")
                    choices = j.get("choices") or []
                    if not choices: continue
                    c = choices[0]
                    delta = c.get("delta") or {}
                    if delta.get("content"): content_parts.append(delta["content"])
                    if delta.get("reasoning_content"): reasoning_parts.append(delta["reasoning_content"])
                    if c.get("finish_reason"): finish_reason = c["finish_reason"]
                    if j.get("usage"): usage = j["usage"]
                    if c.get("usage"): usage = c["usage"]
            finally:
                try: resp.close()
                except: pass
            content = "".join(content_parts)
            reasoning = "".join(reasoning_parts)
            created = int(time.time())
            cid = upstream_id or f"chatcmpl-{uuid.uuid4().hex[:24]}"
            msg = {"role":"assistant","content": content}
            if reasoning:
                msg["reasoning_content"] = reasoning
                msg["reasoning"] = reasoning
            out = {"id": cid, "object":"chat.completion","created": created, "model": req_model,
                   "choices":[{"index":0,"message": msg, "finish_reason": finish_reason or "stop"}],
                   "usage": usage or {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}}
            self.send_json(200, out)
            return

def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"WorkBuddy proxy listening on http://127.0.0.1:{PORT}")
    print(f" auth: {AUTH_FILE}")
    print(f" upstream: {UPSTREAM}")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
