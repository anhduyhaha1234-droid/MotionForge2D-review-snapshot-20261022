# Incoming Skill Pack Analysis (pre-install checklist)

Session-validated workflow (2026-08, hermes-skills.zip research pack) for analyzing user-provided skill packs before installation. The user's explicit workflow: **analyze features first → report required credentials → user supplies them → only then install/use.**

## 1. Extract + read

- `unzip -l` first to see the shape (README, SKILL.md files, references/).
- Extract to a temp dir — on Windows use `C:/Users/Admin/AppData/Local/Temp/...`, NOT `/tmp/` (Python FileNotFoundError trap).
- Read README.md first (pack intent + prerequisites), then every SKILL.md + all `references/`.
- Check name conflicts: `ls skills/<category>/` — a pack skill whose name already exists needs a decision, not an overwrite.
- Check overlap with existing umbrellas (e.g. an incoming deep-research pack vs an installed bom-* research cluster — complementary or duplicative?).

## 2. Readiness probes (READ-ONLY — never configure or test)

| Probe | Command | Interpretation |
|---|---|---|
| Local service up | `curl -s -m 4 http://localhost:PORT/` | 404 on /health but live root (`/dashboard`) = server IS running |
| Provider credentials | Minimal authenticated call to the service's API | `"No credentials for provider: X"` = server up, creds NOT configured on this machine |
| Python dependency | `python -c "import <pkg>; print(<pkg>.__version__)"` | Missing = report as install step, not a blocker |
| Env keys | `env \| grep -i <key>` + grep `config.yaml`/`.env` | Missing = list in credential table |
| Router/gateway config | `AppData/Roaming/<app>/` (e.g. 9router: `auth/cli-secret`, `db/data.sqlite` with `providerConnections` table) | Read-only inspection OK; NEVER add credentials without user approval |

## 3. Deliverable format (matches user's expectations)

- Feature table per skill: role, size, key mechanism.
- Strengths/weaknesses — include compatibility with CURRENT config (e.g. `max_spawn_depth=1` breaks orchestrator fan-out patterns).
- Credential table: `# | credential | used by | required? | where to get` — mark required vs optional clearly (e.g. Jina key required, proxy optional).
- Machine status: what's already present vs missing (service up but unconfigured, package not installed).
- Install plan listed, NOT executed. Include pre-install fixes you found (e.g. soften injection-triggering language in third-party SKILL.md — see hermes-skill-authoring pitfalls).

## 4. Scope discipline (user correction, 2026-08)

The user stopped mid-session with: "phân tích tính năng trước. cần gì credential gì thì bảo tôi cấp chưa cần dùng ngay đâu" — analyze features first; tell me what credentials to provide; no need to use it right away.

- Probing credentials (testing providers, dumping config DBs) BEFORE delivering the analysis is out of scope.
- The user supplies credentials explicitly afterward — do not hunt for them preemptively.
- Vietnamese user: deliver the analysis in Vietnamese with concrete evidence.
