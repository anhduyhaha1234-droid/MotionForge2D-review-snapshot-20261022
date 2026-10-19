# WorkBuddy HY4 Local Proxy — OpenAI compatible

Stdlib-only Python proxy. Reads live auth from your logged-in WorkBuddy app, forwards to `https://www.workbuddy.ai/v2/chat/completions`.

## Run
```
python server.py --port 8787
# or double-click start.bat
```
Health: http://127.0.0.1:8787/health  Models: http://127.0.0.1:8787/v1/models
No API key needed — upstream auth is taken from:
`%LOCALAPPDATA%\CodeBuddyExtension\Data\Public\auth\workbuddy-desktop-ai.info`
(keep WorkBuddy logged in; the proxy reads the file on every request, so token refreshes are picked up automatically).

## OpenAI compat

Base URL: `http://127.0.0.1:8787/v1` — use any OpenAI SDK.

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8787/v1", api_key="sk-workbuddy")
print(client.chat.completions.create(model="hy4-preview", messages=[{"role":"user","content":"say hi"}]).choices[0].message.content)
# streaming:
for chunk in client.chat.completions.create(model="hy4-preview", messages=[{"role":"user","content":"hi"}], stream=True):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

```bash
curl http://127.0.0.1:8787/v1/models
curl http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"hy4-preview","messages":[{"role":"user","content":"say hello"}]}'
curl -N http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"hy4-preview","messages":[{"role":"user","content":"say hello"}],"stream":true}'
```

Models: `hy4-preview` (also `hy4`, `workbuddy/hy4-preview`), `hy3`. All hy4 aliases hit upstream `hy4-preview`.
