# Remote Inspection Checklist — Mnemosyne Session 2026-08-27

Source: `mnemosyne-oss/mnemosyne` deep-dive. Verified via real terminal output.

## Repo Facts (point-in-time 2026-08-27)
- Org: mnemosyne-oss, 2795★ 230 forks, MIT, main branch, created 2026-04-05
- PyPI: `mnemosyne-memory` 3.15.1 (tree 4.0.0b1), Python >=3.10, core dep only PyYAML
- Description: "Zero-cloud AI memory that works everywhere. SQLite-backed. One pure-Python dependency."
- Languages: Python 5.7M (99.5%), TypeScript 24k
- BEAM tiers: working_memory (FTS5, TTL 168h, 10k) → sleep() → episodic_memory (hybrid 50% vec +30% FTS +20% importance) + scratchpad (1k, non-searchable) + TripleStore (temporal KG)
- MCP: 29 tools, 3 transports (stdio/SSE/streamable-http /mcp), non-loopback requires MNEMOSYNE_MCP_TOKEN + MNEMOSYNE_MCP_ALLOWED_HOSTS
- Tests: 191 files under tests/

## Per-Repo Checklist (copy per inspection)
- [ ] api.github.com/repos/<owner>/<repo> → stars/forks/pushed/language/description
- [ ] /languages + pypi.org/pypi/<pkg>/json (if Python)
- [ ] raw README + pyproject.toml (try main then master)
- [ ] api contents?ref=main → top-level file list
- [ ] shallow clone only if README insufficient → inspect core/ + docs/architecture.md + __init__.py version
- [ ] benchmarks: preserve version label + judge caveat verbatim
- [ ] clean clone (rm -rf + verify)

## What "làm gì" Answer Must Contain
Purpose | Architecture (BEAM or equivalent mental model) | Key modules | Integrations | Benchmarks with caveats | Install one-liner
