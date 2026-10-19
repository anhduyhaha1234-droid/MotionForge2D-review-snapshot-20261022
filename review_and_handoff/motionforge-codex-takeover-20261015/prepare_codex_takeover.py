from pathlib import Path
import hashlib, json, shutil, datetime, urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/motionforge-codex-takeover-20261015'
INV = ROOT / 'work/hermes-skill-inventory-20261015'
MAIN = Path('C:/Users/Admin/MotionForge2D')
RUN = Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long')
R6 = RUN / 'tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')
def dump(p, d): write(p, json.dumps(d, ensure_ascii=False, indent=2)+'\n')

inventory = json.loads((INV/'HERMES_SKILL_INVENTORY.json').read_text(encoding='utf-8'))
copied = []
for skill in inventory['selected_skill_directories']:
    for f in skill['files']:
        src = Path(f['source']); dst = OUT/'skills/vendor/hermes'/f['relative_path']
        if sha(src) != f['sha256']: raise RuntimeError('source changed: '+str(src))
        if dst.exists() and sha(dst) != f['sha256']: raise RuntimeError('destination conflict: '+str(dst))
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists(): shutil.copy2(src, dst)
        assert sha(dst) == f['sha256']
        copied.append({'source':str(src),'destination':str(dst),'sha256':f['sha256'],'bytes':dst.stat().st_size})
for name in ['HERMES_SKILL_INVENTORY.json','ACTIVE_DIGEST_VI.md','REPORT_VI.md','SELECTED_SKILL_NAMES.txt']:
    shutil.copy2(INV/name, OUT/'skills'/name)
dump(OUT/'skills/HERMES_IMPORT_RECEIPT.json', {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'skills':len(inventory['selected_skill_directories']),'files':copied,'verified_count':len(copied)})

skills = [
 ('verification-before-completion','obra/superpowers','bb92a77741419a4ab5f06e711a283343f1ada0c3'),
 ('systematic-debugging','obra/superpowers','bb92a77741419a4ab5f06e711a283343f1ada0c3'),
 ('writing-plans','obra/superpowers','bb92a77741419a4ab5f06e711a283343f1ada0c3'),
 ('receiving-code-review','obra/superpowers','bb92a77741419a4ab5f06e711a283343f1ada0c3'),
 ('context-compression','muratcankoylan/Agent-Skills-for-Context-Engineering','9ff0c99108b36d3b886defd825d8ac1f47dba374')]
lock=[]
for name, repo, ref in skills:
    src=Path('C:/Users/Admin/.codex/skills')/name
    dst=OUT/'skills/vendor/github'/name
    files=[]
    for f in src.rglob('*'):
        if not f.is_file(): continue
        d=dst/f.relative_to(src); d.parent.mkdir(parents=True,exist_ok=True)
        if not d.exists(): shutil.copy2(f,d)
        assert sha(d)==sha(f)
        files.append({'path':str(d.relative_to(OUT)),'sha256':sha(d),'bytes':d.stat().st_size})
    raw=f'https://raw.githubusercontent.com/{repo}/{ref}/skills/{name}/SKILL.md'
    remote=urllib.request.urlopen(raw,timeout=30).read()
    local=(src/'SKILL.md').read_bytes()
    assert remote.replace(b'\r\n',b'\n')==local.replace(b'\r\n',b'\n'), name
    lic=urllib.request.urlopen(f'https://raw.githubusercontent.com/{repo}/{ref}/LICENSE',timeout=30).read()
    (dst/'SOURCE_LICENSE.txt').write_bytes(lic)
    lock.append({'name':name,'repo':repo,'commit':ref,'source':f'https://github.com/{repo}/blob/{ref}/skills/{name}/SKILL.md','installed_path':str(src),'remote_skill_sha256':hashlib.sha256(remote).hexdigest(),'installed_skill_sha256':sha(src/'SKILL.md'),'remote_exact_bytes':remote==local,'remote_lf_normalized_equal':True,'line_ending_note':'Git sparse checkout may use Windows CRLF; normalized comparison preserves all text.','license':'MIT','license_url':f'https://github.com/{repo}/blob/{ref}/LICENSE','license_sha256':hashlib.sha256(lic).hexdigest(),'files':files})
dump(OUT/'skills/SKILL_SOURCE_LOCK.json',lock)
write(OUT/'skills/README_VI.md', '''# Thư viện skills MotionForge2D

Đã import byte-identical 40 thư mục Hermes liên quan dự án (551 file), chọn từ171 skills. Manifest giữ source, SHA256 và mức độ đọc:21 đọc đầy đủ,3 đọc một phần,16 chỉ index. Toàn bộ tài liệu được lưu để truy xuất theo task; không nhét tất cả vào context.

Đã cài5 skill GitHub vào Codex và sao chép bản ghim vào thư viện này. SKILL_SOURCE_LOCK.json xác minh nguồn GitHub, commit, license và hash từng file. Bốn SKILL.md khớp exact bytes; context-compression qua git trên Windows có CRLF, khớp toàn bộ nội dung sau chuẩn hóa LF. Đây là community skills, không gắn nhãn official OpenAI/Anthropic.

Áp dụng ACTIVE_DIGEST_VI.md dưới canonical rules và chỉ thị user. Không thực thi scripts/hooks khi import. Không áp các chỉ dẫn đổi model, tự commit/push, hỏi lại approval đã có, tự mở thêm workers, hoặc total caps lịch sử. Skill writing-plans được dùng để chia việc; user đã chọn cách thực thi nên không cần một vòng xin duyệt kế hoạch mới. Skill verification áp đúng claim, không bắt render GPU lại cho mọi sửa CPU. Context sử dụng checkpoint theo task; không bịa phần trăm context. compression_evaluator.py là demo heuristic, không là quality gate.

## Nguồn5 skill đã cài
'''+'\n'.join(f"- [{n}](https://github.com/{r}/blob/{v}/skills/{n}/SKILL.md)" for n,r,v in skills)+'\n')

overlay='''### 0.11. Codex coding takeover theo user15/10/2026

User yêu cầu nạp skills Hermes, bổ sung5 skills, tạo sub-agent coding và root
review độc lập; user xác nhận **GPT-6 Sol / Max**. Quyền mới thay thế các hạn chế
"Codex chỉ review/không dispatch", owner Hermes bắt buộc và model cũ riêng cho
lane Codex được giao dưới đây. Không khởi động lại Hermes hay đổi session cũ.

- Root là PM/reviewer; một coding owner dùng `gpt-6-sol`, reasoning `max`, không
  fallback. Coder được tự review, sửa findings trong allowlist và chạy kiểm tra;
  chỉ root được APPROVED đúng candidate/microtask sau kiểm tra độc lập.
- WIP1 và GPU1, source/CAST/style pins, frozen evidence, patch-only/preimages,
  semantic acceptance và canonical Q01–Q12 giữ nguyên. Không commit/push/reset/
  stash/clean; không mở UI/full22 trước gate pilot. Chỉ task đang active được ghi.
- Trước owner transfer: xác minh old launcher/children terminal, queue/runner
  quiet, reconcile stale lease bằng helper hiện có dưới controller mutex, giữ
  preimage và receipt. ALIVE/UNKNOWN còn lại phải block production writes.
- C01 đầu tiên: sửa integrity của semantic review binding trong r6_gate.py và
  focused regression/consumer tests; CPU only, không render hay ghi review PASS.
  C02 cache/event/child outcome, C03 evidence/media, rồi pilot acceptance và
  integration là dependency roadmap, không phải quyền ghi đồng thời.
- Mỗi task dùng packet gọn, source index và2–4 skills liên quan. Lưu checkpoint
  sau mỗi patch/test unit, trước large read/compaction, khi provider lỗi: goal,
  task/owner/model, allowlist, exact file/hash, tests/exit, decisions, blockers,
  next command và live jobs. Không suy context percent từ message counts.
- Correction resume cùng coder. Context mới chỉ sau writer cũ terminal, durable
  handoff, preflight và root điều phối; giữ counters/history, không dùng reset
  session để né quota. Root kiểm lại actual bytes trước khi tiếp tục.
- Quota5h/tuần và workspace credits là các tín hiệu khác nhau. Báo lỗi thực tế
  tại chat gốc, ghi reset time nếu API có; không tự mua/reset credits/đổi model.
  Khi có quota, tiếp tục từ checkpoint với cùng scope. Heartbeat thông báo khi
  trạng thái đổi; không hứa vẫn chạy được lúc account bị chặn hoàn toàn.
- Không đặt total deadline/candidate/continuation caps mới. Chia task để giảm
  context không được dùng để đóng dự án khi acceptance còn fail/unknown.

Packet hiện tại: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015/`.
PROJECT_STATE.json/checkpoints giữ state; file này vẫn là canonical rules duy nhất.

'''
rules=MAIN/'docs/pm/HERMES_AUTOPILOT_RULES.md'
raw=rules.read_bytes()
if b'### 0.11.' not in raw:
    baseline=json.loads((OUT/'PREFLIGHT.json').read_text(encoding='utf-8'))['preimages'][str(rules)]
    assert sha(rules)==baseline['sha256'], 'rules changed since preflight'
    marker='## 0. Chế độ hiện hành'.encode('utf-8')
    assert raw.count(marker)==1
    rules.write_bytes(raw.replace(marker,overlay.encode('utf-8')+marker,1))

for name in ['CODEX_PM_HANDOFF.md','ROADMAP.md']:
    p=MAIN/'docs/pm'/name; data=p.read_bytes()
    heading='### Codex takeover15/10/2026 — C01, user-authorized\n\n'
    if heading.encode() not in data:
        note=heading+'User xác nhận GPT-6 Sol Max cho một coding sub-agent; root độc lập review. R6g14/10 đã chạy nhưng chưa nộp final/new master, parent vẫn NOT_APPROVED. Đọc rules§0.11 và packet `'+str(OUT).replace('\\','/')+'`; state/next command ở PROJECT_STATE.json. Reconcile old stale lease trước production write; C01 CPU gate binding, các bước sau phụ thuộc review. Skill inventory/import không thay acceptance video.\n\n'
        idx=data.find(b'\n')+1; assert idx>0
        p.write_bytes(data[:idx]+b'\n'+note.encode()+data[idx:])

task=f'''# C01 — Complete semantic review input binding

Authority: user15Oct explicitly requests Codex coding + independent root review,
selects gpt-6-sol / max. Read MAIN/AGENTS.md, SESSION_PROTOCOL.md, the full canonical
HERMES_AUTOPILOT_RULES.md (including0.11), this packet and skills/ACTIVE_DIGEST_VI.md.
MAIN={MAIN}
RUN={RUN}
R6={R6}
OUT={OUT}

Goal: a review with missing or malformed dependency binding cannot authorize the
actual assembly consumer. Current require_review iterates only recorded inputs;
omitting deps_sha can bypass dependency identity. Reproduce current bytes first.
No semantic quality claim from this engineering correction.

Write allowlist: R6/scripts/r6_gate.py; a new R6/tests/test_codex_c01_review_binding.py;
OUT/c01-worker/** (checkpoint, preimages, fixtures, tests/output/diff). Change
r6_assemble.py only if a reproduced consumer-wiring defect requires it; report why.
All other production files, historical evidence/reviews/media, runtime/model/DB/
registry/PM files are read-only. Never rewrite/delete existing tests or artifacts.
Root owns PM/lease reconciliation; require OUT/OWNERSHIP_PREFLIGHT.json with ok=true
before production edits. If absent, inspect and reproduce only in isolated fixtures.

Implementation sequence:
1. RULES_LOADED; preflight SHA/size/lines and preimage relevant existing files.
   Read existing gate callers/review writers/schema/examples and existing tests.
2. Reproduce the missing-input bypass and malformed records on current code with
   realistic fixtures; save raw commands and outputs under c01-worker. No GPU.
3. Small patch: validate complete nonempty current/recorded dependency mappings,
   required typed fields and exact review/artifact identity. Reject subset,
   mismatched, empty and malformed records with GateBlock diagnostics. Keep valid
   current producer schema compatible; do not invent a parallel review protocol.
4. Meaningful regression tests: valid positive; omitted current dependency;
   changed dependency; stale artifact; wrong artifact path/review identity;
   malformed JSON/types/frames. False values must not pass by string coercion.
   Actual gate_assemble path must reject invalid records before copying/encoding;
   include one real assembly main call with isolated K paths and encoder tripwire
   (no production output writes), not merely a mock that makes gate throw.
5. Run focused tests and relevant existing gate tests; self-review AC, correctness,
   compatibility, write scope, failure paths; fix within allowlist. Save exact
   candidate hashes + diff against preimages. Submit TASK_SUBMITTED and stop writing
   for root's independent review. Do not mark whole Q05/video/project APPROVED.

Skills to load now (local, actual installed): systematic-debugging,
verification-before-completion, receiving-code-review under
C:/Users/Admin/.codex/skills/<name>/SKILL.md. Apply compact context/checkpoint
contract here; library includes context-compression and Hermes source on demand.
No required meta-superpowers install, automatic commit or new approval round.

Context: one task outcome per context; only targeted reads, raw large logs to disk.
Checkpoint after every coherent patch/test unit or before context pressure, using
intent/current state/files+hashes/decisions/tests+exit/remaining/next command/jobs.
No context percentage claims without telemetry. No subagents. No model fallback.
On quota/credit error, preserve exact error and state; return BLOCKED_QUOTA with
known reset info only. Root notifies original chat; no tight retries.

Root review after writer terminal: inspect diff, run fresh negative/positive probes
and consumer integration independently; route corrections back to this same owner.
No production render until gate review accepted and GPU lease acquired separately.
Start now with preflight + reproduction, then implement; do not stop at a plan.
'''
write(OUT/'TASK_C01.md',task)
dump(OUT/'PROJECT_STATE.json',{'schema':1,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':'MotionForge2D','parent':'MF-DEMO-LONG-01','parent_status':'NOT_APPROVED','task':'CODEX-C01-REVIEW-BINDING','status':'PREPARED_PENDING_LEASE_RECONCILIATION','model':'gpt-6-sol','reasoning':'max','owner':None,'root_role':'independent PM/reviewer','active_writer':False,'task_packet':str(OUT/'TASK_C01.md'),'current_baseline':'R6g actual bytes; no new R6g master submitted','next_action':'Reconcile stale R6g lease under controller mutex, dispatch one gpt-6-sol max coder with TASK_C01.md','quota':{'research_agents_error':'Your workspace is out of credits. Ask your workspace owner to refill in order to continue.','context_remaining':'UNKNOWN'},'roadmap':['C01 complete review input binding','C02 cache/event/child outcome correctness after C01 review','C03 evidence and media correction after engineering gates','300s pilot independent semantic acceptance','tool integration and full-source scope after pilot approval'],'checkpoint_contract':['intent','files+hashes','decisions','test commands+exit','remaining','next command','live jobs'],'no_fallback':True})
print(json.dumps({'hermes_imported':len(copied),'skills_installed_verified':len(lock),'packet':str(OUT),'rules_sha256':sha(rules)}))
