---
name: remote-repo-analysis
description: Analyze remote GitHub repos when URL extraction fails.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [github, repository, inspection, landscape, windows, msys]
---

# Remote Repository Analysis

Inspect **remote** GitHub repositories you have never cloned — reliably, even when chat `@url:` extraction returns `no content extracted` and on Windows/MSYS where `/tmp` is not visible to native binaries.

## When to Use

- User pastes `@url:https://github.com/<owner>/<repo>` and asks "phân tích git này làm gì"
- You need to answer "what does this repo do" without prior local clone
- `@url` extraction returned empty and you must fall back
- You are on Windows (git-bash/MSYS) and `/tmp` clones disappear

## Workflow (3 Phases)

### Phase 1: Lightweight API Probe (no clone)

```bash
# repo metadata — stars, language, description, pushed_at, license
curl -sL "https://api.github.com/repos/<owner>/<repo>"

# languages breakdown
curl -sL "https://api.github.com/repos/<owner>/<repo>/languages"

# PyPI (if Python) — installed version, deps, keywords
curl -sL "https://pypi.org/pypi/<package>/json" | python -c "import sys,json; d=json.load(sys.stdin); print(d['info']['version'], d['info']['summary'])"

# README + pyproject without cloning (try main then master)
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/README.md" | head -n 200
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/pyproject.toml" | head -n 120

# top-level file list
curl -sL "https://api.github.com/repos/<owner>/<repo>/contents?ref=main" | grep -o '"name":"[^"]*"'
```

> Unauthenticated rate limit: 60 req/hour. Batch calls.

### Phase 2: Shallow Clone (when README is insufficient)

```bash
# On Windows/MSYS do NOT use /tmp — native python/node cannot see it
# Prefer CWD or native Temp
git clone --depth 1 https://github.com/<owner>/<repo>.git ./<repo>-inspect
ls -1 ./<repo>-inspect/mnemosyne/core/   # or top-level
head -n 80 ./<repo>-inspect/mnemosyne/__init__.py
head -n 100 ./<repo>-inspect/docs/architecture.md
rm -rf ./<repo>-inspect  # clean up — verify with ls
```

MSYS mapping reminder: `terminal` runs via MSYS bash. `/tmp` → MSYS temp, `C:/Users/<user>/AppData/Local/Temp/` → native temp. Always clean the clone and confirm `cleaned:0`.

### Phase 3: Architecture-Aware Report

Do not stop at stars/push-date. For the class of repo (memory layer, agent framework, etc.) report:

1. **Purpose (1 line)** — tagline + PyPI summary
2. **Core architecture** — storage model (e.g. BEAM: working/episodic/scratchpad), search (vector+FTS), process model
3. **Key modules** — top-level + `core/` list, test count
4. **Integrations** — platforms supported (MCP transports, SDK)
5. **Benchmarks/comparison** — quote point-in-time labels honestly, note judge/metrics caveats
6. **Install quick-start** — `pip install` + minimal code

Reference: `references/remote-inspection-checklist.md` for the per-repo checklist, and `references/windows-msys-paths.md` for path pitfalls.

## Decision Rules

- Always run Phase 1 first — 80% of "what does it do" is answered without cloning
- If `@url` was empty, say so and show the API+clone proof — never claim "repo not found"
- On Windows, never `git clone` to `/tmp`; use `./<name>-inspect`
- Map `main` vs `master` via contents API before assuming `main`
- Treat README claims as hypothesis — verify via `pyproject.toml` / `__init__.py` version and `ls core/`

## Pitfalls

- **@url empty ≠ repo missing.** Chat URL extractor often returns `no content extracted` for github.com. Fall back to `api.github.com` + `raw.githubusercontent` + shallow clone before concluding.
- **MSYS /tmp invisibility.** `terminal`'s `/tmp` is not `C:\Users\...\AppData\Local\Temp`. Clones there yield `FileNotFoundError` in Python/Node. Use CWD.
- **Reporting stars without architecture.** Users asking "làm gì" want the mental model (e.g. BEAM tiers, hybrid search weights) not just `2795★`.
- **Benchmark misreading.** Always preserve version labels and judge caveats from README (e.g. "v3.0.0 May 2026, different judges not comparable").
- **Leaving clones behind.** Hidden tests inspect final disk state — always `rm -rf` the inspect dir and verify.

## Verification

- [ ] `@url` emptiness acknowledged with fallback proof
- [ ] Repo metadata fetched via API (stars, language, description shown)
- [ ] README + pyproject or `__init__.py` version inspected
- [ ] Clone (if used) created at native-visible path and removed before finish
- [ ] Report covers purpose + architecture + modules + integrations + install
