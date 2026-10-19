Đọc TOÀN BỘ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` trước preflight hoặc ghi file. Báo RULES_LOADED kèm đường dẫn, HEAD thực tế và các mục đã nạp, đặc biệt §0.12, §4, §8.2 và §10.1. Đọc thêm MAIN/AGENTS.md, docs/pm/SESSION_PROTOCOL.md, CODEX_PM_HANDOFF.md và ROADMAP.md. Không dispatch bằng trí nhớ.

Bạn là implementation owner của MotionForge2D, tiếp tục **MF-DEMO-LONG-01/G1-R1** trong đúng Hermes session **20261017_115944_b2a338**. Đây là correction candidate03 → candidate04. Codex là reviewer cuối. Bạn được code, tự review và sửa trong phạm vi dưới đây; không tự phê duyệt G1/G2/G3.

## 1. Kết quả cần đạt

Hoàn thành các lỗi engineering đang chặn video, nộp một candidate đủ để Codex review. Đích sản phẩm vẫn là nguồn → reskin → QC → xuất video thật qua app. Không chuyển sang làm template launch video, thêm trang trí UI hoặc viết báo cáo thay cho sản phẩm.

Candidate03 nhận **CHANGES_REQUESTED**. Root xác minh 8/20 hàng acceptance; 12 hàng còn mở hoặc một phần. 17/17 manifest hashes khớp, focused asset suite 10/10 đạt. Claim 89/89 không thay thế các lỗi thực tế: render hợp lệ bị NameError; tên frame không khớp upstream; video giả vẫn PASS; artifact đổi bytes nhưng giữ size vẫn TASK_SUBMITTED; final adapter chưa truyền artifacts.

G1 chưa APPROVED. GPU, media mới, full source và app integration chưa được mở. Phần video phía dưới là kế hoạch chờ gate, không cho phép bạn tự vượt gate.

## 2. Required reading

Review packet hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-03-20261019/`

Đọc REVIEW_VI.md, CORRECTION_MATRIX.md, RESEARCH_DECISIONS_VI.md, SESSION_OPENING_PROPOSAL.md và vision/README_VI.md. Dùng raw evidence: ROOT_PROBES.json, EXTRA_PROBES.json, PROPAGATION_BOUNDARIES.json, EVENT_CONTROLS.json, delegated_audit/PROBE_RESULTS.json, RUFF_F821.json, Q11_BINDING_AUDIT.json. Không ghi đè packet này. Scripts root có output cố định: chỉ đọc hoặc copy sang sandbox mới rồi đổi output paths, không chạy lại vào review folder.

Binding product/technology contract:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/PROMPT_GEMINI_MOTIONFORGE_VI.md`.

Giữ Q01–Q12, T01–T15, source/cast/style/audio/runtime pins và G1 → G2 → G3. Chỉ nạp skill debugging, receiving-code-review, verification và context có liên quan. Không nạp toàn kho skills hoặc toàn transcript.

## 3. Model, owner và preflight

Giữ `ag/gemini-3.8-flash-high`, provider custom, endpoint `http://127.0.0.1:20128/v1`, cấu hình high hiện có, fallback OFF. Không đổi model/account/global router để né quota. `gemini-implementation-owner` chỉ là label; SID thật nằm ở đầu prompt.

Trước write, kiểm actual turn/process PID + creation time, children, watcher, controller lease và Comfy queue. Daemon còn sống không chứng minh writer đang làm việc. Không mở resume thứ hai, không kill đại trà hoặc xóa lock. Ownership chưa rõ phải được reconcile trước.

Kiểm context health: diễn giải đúng ba nhóm P1 bằng raw proof, thay vì lặp lại “20/20 đã đóng”. Context dài một mình không cho phép chuyển owner. Nếu có bằng chứng lặp lại về sai current contract hoặc destructive incident, freeze và báo Codex quyết định recovery; không tự tạo replacement writer.

Đọc Git HEAD/branch/dirty attribution ở MAIN và INTEGRATION. HEAD root quan sát là a40e368f7c47c232cf2eeed9fb185c5972cb98ba, cần kiểm lại; đây không phải lệnh checkout. Không commit/push/merge/reset/clean/stash/restore.

Trước patch: tạo manifest SHA256/bytes/lines/mtime của write-set và protected set, snapshot byte-for-byte rồi xác minh hash. File hiện hữu chỉ bounded patch có exact preimage. Sau patch kiểm hash, diff, shrink. Missing/destructive shrink → freeze, không dựng lại bằng memory.

## 4. Write-set và phân công

R6 = `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6`.

EX = `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution`.

Được patch:

- R6/scripts/r6_propagate.py, r6_event_contract.py, r6_evidence_contract.py, r6_matrix.py, r6_gate.py.
- r6_cotracker.py và r6_ledger.py khi đóng M06/M11. r6_cache.py, r6_key_recipe.py, r6_keygen_asset.py, r6_assemble.py chỉ khi actual repro buộc sửa; ghi impact và preimage trước, giữ các phần đã đạt.
- EX/G1-R1/r6_submission_adapter.py: dùng đúng path đang tồn tại, khai báo attribution rõ; không sửa historical terminal writer.
- R6/tests/test_g1_r1_*.py. Existing tests liên quan chỉ bổ sung hoặc sửa fixture theo contract thật; không bỏ, skip hoặc nới assertion để xanh.
- New fixtures, raw receipts, checkpoints trong EX/G1-R1/continuations/<unique-id>/; new packet EX/submissions/g1-candidate-04/ hoặc ID chưa tồn tại.
- EX/STATE.json, CHECKPOINT.json, RESUME.md sau preimages. Coordination-only patch EX/auto_nudge_watchdog.py và telegram_heartbeat.py để sửa truthfulness/quota policy; không mở lịch mới hoặc gửi thông báo thật chỉ để test.

Protected: MAIN, INTEGRATION, production DB, Hermes DB, router config/runtime, weights, source, CAST, R4/R5/vendor, historical outputs/receipts/terminals/controller production và mọi root review packet. DB chỉ read-only. Không sửa historical proof 34/34 hoặc 51/51. Dependency ngoài allowlist cần exact path/repro để Codex mở scope trước.

Tối đa một production writer, GPU=0 ở G1. Nếu native delegation và quota thực sự khả dụng, được tạo hai task QA read-only mới: `G1-R1-QA-PROPAGATION-04` và `G1-R1-QA-EVIDENCE-04`, mỗi task một child session, ghi ID thật, cùng model route. Mỗi QA chỉ ghi own EX continuation/qa/<task>/, đọc immutable snapshot và dùng fixture riêng. Hai QA có thể chạy đồng thời vì không chung write-set hoặc mutable resources. Manager/QA không sửa production/test/state.

Nếu delegation không khả dụng, ghi thật và owner self-review tuần tự. Không giả sub-agent, không tạo child/model khác để né quota. Global gate chờ writer frozen; QA phải đối chiếu hash mới nhất sau writer terminal.

## 5. Sửa hết nhóm lỗi trong cùng correction

**R04 — render và failure boundary.** Import Image đúng scope. Dùng global frame naming beg..end−1 của pinned VideoSequence: beg11/end21 phải nhận 0011..0020. Không đổi tên theo vị trí để che sai frame. Failure handling phải bao preflight, planner, staging, child, merge, decode và finalize, gồm expected SystemExit khi thiếu key. Failure phải nonzero, có receipt, không để stale success manifest usable; giữ failed bytes. Test actual CPU child: valid một run, hai run với beg>1; rc7, partial, wrong/extra names, corrupt image, missing key và preflight failure. Đường valid phải thật sự đạt; không chỉ mock run_one rc7.

**R03/R05 — contract thời gian.** Parser chung phải strict integer, từ chối bool/float/coerced string, kiểm f/frame conflict, bounds, contact order, missing metadata. Giữ frame43 →43, f700 bị reject; actual tracker invisible →null, good →0, offset10 →10. Hoàn thiện M06 về shape/type/finite/canvas/query/time và paired input identity. Với cuts: chứng minh frozen shot boundaries đã bao mọi cut và reject intra-shot cut, hoặc wire canonical producer →ledger→run_shot→planner. Không phát minh schema chỉ để test hoặc truyền [] rồi nhận đã đóng.

**R06 — bằng chứng thật.** Thay ftyp/size heuristic bằng ffprobe và FFmpeg decode đã cài. Kiểm frame count/fps/duration/streams/audio/timebase theo loại artifact; dùng CPU fixture ngắn ở G1, không render pilot. Receipt phải bind artifact/source/invocation hashes. Q05 phải bind executed command, exit, node IDs, source/test/input hashes; all_passed và file size không đủ. Q07 phải phủ current required deps, không lấy một record bất kỳ từ shared work. Q01 phải bind image hash/source/cast/invocation/shots/coverage; PNG decode được không đồng nghĩa semantic PASS. Forge, stale, wrong invocation, unrelated coverage và duplicate PASS labels phải bị chặn. Media Q giữ UNKNOWN/FAIL thật đến G2.

**R07 — actual submission.** Current adapter đọc cùng namespace/manifest, recompute mọi hash + size + required kind + identity trước publish. Valid positive phải qua. ABCD→WXYZ cùng size phải bị reject; lỗi phải exit nonzero và không TASK_SUBMITTED. Final caller phải truyền artifacts. Freeze theo thứ tự không vòng lặp: artifacts/matrix →manifest→terminal hoặc commit marker tham chiếu manifest. Không hash manifest vào chính nó hoặc sửa matrix sau khi hash. Inject failure ở các phase; partial/mixed submission không được consume. Chỉ manifest current artifact set, không quét cả lịch sử R6. Historical writer giữ nguyên làm negative control.

**R08 — concurrency provenance.** Map 51/51 và 34/34 cases đến actual source/runtime/harness/raw/current hashes, gồm PID creation time, UNKNOWN, detached child, cancel và release. Historical proof đúng bytes đủ coverage thì dùng VERIFIED_UNCHANGED, không rerun vô cớ. Toy O_EXCL không thay contested operation của controller. Chỉ chạy missing subset trong clone với MF_RUN_ROOT riêng nếu thực sự thiếu; không chạy historical script có hardcoded output/rmtree trên live. Chứng minh hai process sống tại barrier, bounded joins, một winner/một child, đầy đủ ledger và lease released.

**R09 — state và packet.** Reconcile references candidate01/02/03, next_command, open rows, test duration, changed files/adapter path và owner registry. Không tự ghi root_status CLOSED hay 20/20. Watchdog pending review không gọi model; auth/quota không blind retry, connection error chờ ít nhất năm phút đúng rules. Productive progress phải dựa trên delta/artifact thật, không mtime đơn thuần. Freeze cả source/test/support bytes và bind tất cả vào manifest; raw commands/exits/node IDs/assertions phải tái hiện được, không chỉ summary hardcode.

Mỗi nhóm phải ghi symptom → actual failing call path → root cause → test blind spot → PATCH/REUSE/REPLACE/DEFER → evidence trên cùng fixture. RESEARCH_DECISIONS_VI.md đã kiểm Pydantic 2.13.5, ffprobe 8.1.2, Ruff 0.16.0 và pinned VideoSequence. Lỗi adapter/contract chưa chứng minh cần thay video engine. Nếu đề xuất upstream khác, nêu official URL/version/license/compatibility và cùng-source comparison; GPU benchmark chỉ sau gate. Không cài toàn shortlist.

## 6. Vision đã có đường dùng được

Đọc vision/README_VI.md trong review packet. Helper đã được thử live thành công:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-03-20261019/vision/motionforge_vision_qc.py`.

Dùng `C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe -B`, lặp --image/--label cho source, CAST và candidate cùng frame; --out trỏ receipt mới trong own invocation. Helper gọi đúng Gemini qua 9router, không fallback hoặc tự retry, lưu image hashes và structured issues. Exit0 chỉ transport OK; đọc analysis_json và giữ UNKNOWN khi thiếu evidence. Không patch helper frozen; wrapper mới nếu cần đặt trong own EX continuation.

Native Hermes vision_analyze tool-message đã timeout trong root trial; native video/audio chưa được xác minh. Không claim đã xem/nghe clip bằng tool này, không đổi global config. Đường helper nhận pixels đã chạy. Không lặp smoke ở mỗi heartbeat. Ở G1 chỉ chuẩn bị rubric, labels, sample/held-out coverage bằng CPU fixtures; không dùng vision để tự mở media gate.

## 7. Kế hoạch video chờ G1 approval

Chỉ khi Codex có **G1 APPROVED cho exact bytes và explicit media authorization**, mới activate task `MF-DEMO-LONG-01/B-MEDIA` bằng new owner/session được registry ghi. Codex sẽ chốt packet/session; prompt này chưa tự mở task đó. WIP1/GPU1, invocation mới dưới R6/continuations, bảo toàn old master/comparison.

**B1:** Giữ source, CASTB, flat2D style và runtime pins. Kiểm hard cases S0022/S0031/S0033/S0057/S0061/S0062/S0063/S0064/S0073, bảo toàn cải thiện S0074 và phủ những case khác trong ledger. Thực thi SAM2 actor masks, FLUX reference causality, CropAndStitch transform, VACE 4n+1/Trim3/paired perturbation, Rerender/EbSynth event spans, CoTracker contact windows theo T01–T15. Reuse đúng reviewed bytes; chỉ invalidate và render lại descendants bị ảnh hưởng. Khi mất kết nối, tìm existing queue job trước resubmit.

**Vòng QC bắt buộc:** source + immutable CAST + candidate cùng fid → vision ghi lỗi theo frame/region/severity → xác định lỗi input/mask/pose/prop/contact/timing → sửa nguyên nhân → render lại phần ảnh hưởng → kiểm lại cùng fixture và held-out. Xem first/mid/last mỗi shot và before/contact/hold/release/entry/occlusion. Giữ comparison clips playable để xem chuyển động liên tục. Sampled frames không thay toàn bộ video/audio review; capability thiếu thì UNKNOWN, không bịa PASS.

**B2:** Pilot nguồn 01:34–06:34, global frames [2820,11820), 54 shots S0021–S0074, 9000 frames, 30fps, 640×360, đúng 300s, original audio và đúng cut/action timing. Không đổi tên old master hoặc lặp clip cho đủ thời lượng. Nộp playable MP4, source/old/new comparison đồng bộ, indexed contact sheets, event clips, ffprobe/full-decode/AV logs, manifest, coverage đã xem/nghe và resource/wall-time evidence.

Tự review và sửa toàn bộ batch B đến acceptance hoặc blocker thật, không report mỗi shot. Cuối B freeze, dừng writer/children và nộp SELF_VERIFIED_PENDING_CODEX_G2. Chỉ G2 root approval mới mở full source/app integration.

Sau G2, Codex chốt product workspace và task packets Gói C. Đích cuối: app flow Import→Objects→NewLooks/Demo→Apply→Review→Export; persistence/reopen/recovery; full source 39634 frames và original audio; export 1080p/4K phân biệt upscale/native; G3 review độc lập. Chưa có quyền sửa MAIN/UI hoặc full render ngay. Không mở thêm backlog ngoài Phase1.

## 8. Verification, quota và điểm dừng

Runtime G1: `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe -B`. C01_WORKER_DIR, C02A_WORKER_DIR, C02B1_WORKER_DIR, C02B2_WORKER_DIR và C02B3_WORKER_DIR trỏ sandbox mới. CPU tests không dùng live DB, GPU hoặc external model calls.

Ruff sẵn tại `C:/Users/Admin/AppData/Local/Programs/Python/Python311/Scripts/ruff.exe`; chạy check --no-cache --select F821 trên đúng scripts. Thứ tự: micro actual negative + valid positive → 20 rows có raw assertions → focused/static → final relevant suite 89 và tests mới. Không broad legacy discovery trên live tree khi micro còn fail. Record command/cwd/runtime/start/end/exit/source hashes/node IDs/stdout/stderr.

Mỗi phase chỉ giữ current finding, call path, repro và dependency cần thiết. Checkpoint sau outcome coherent, trước compaction/resume: landed delta/hash, open rows, owner/children và exact next command. Không gửi toàn transcript cho child.

Heartbeat20 phút khi có task active; tám phút không có tiến triển thì audit PID/log/queue. Phân biệt quota5h/tuần, workspace credits, auth và route/config errors. Lưu checkpoint và báo blocker thật; không mua/reset/fallback/tạo owner/account để né quota. Connection transient retry đúng rules, chờ năm phút, giữ model/session. WAITING_CODEX_REVIEW không model-nudge hoặc mở lịch mới. Không tự đặt trần tổng budget mới; tiếp tục trong scope tới acceptance, blocker thật hoặc user stop.

Nộp candidate04 immutable: REPORT_VI, MANIFEST có source/support snapshots, actual DIFF, raw TEST_RESULTS/node IDs, matrix20 rows, root cause/reuse decisions, SELF_REVIEW, STATE snapshot, CHECKPOINT, RESUME, LIVE_JOBS và protected hash check. Mỗi PASS trỏ assertion receipt, thiếu gì ghi đúng đó.

Trạng thái cuối: **SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.** Dừng writer/children chờ Codex. Không tự mở media. Bắt đầu preflight và thực hiện correction ngay khi user giao prompt vào exact session; chỉ report candidate đủ review hoặc blocker thật, không dừng sau kế hoạch.
