Đọc TOÀN BỘ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` trước preflight hoặc ghi file. Báo RULES_LOADED với path/HEAD/sections; áp dụng §0.12,§4,§8,§10.1. Đây là correction tiếp cùng task, không approval G1/media/product.

Bạn là implementation owner Gemini của MotionForge2D, actual Hermes session `20261017_115944_b2a338`. Tiếp tục MF-DEMO-LONG-01/G1-R1, chuẩn bị candidate03. Codex đã review candidate02 và kết luận CHANGES_REQUESTED. Không restart dự án; không tự nói20/20PASS hoặc “đóng trọn findings” từ test count. Root xác minh5/20rows;15rows còn mở/thiếu chứng cứ. Có sửa được lỗi thật, phải giữ các phần đã tốt.

## Required reading và quyền hạn

Review packet hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-02-20261018/`

Đọc REVIEW_VI.md, CORRECTION_MATRIX.md, RESEARCH_DECISIONS_VI.md, SESSION_OPENING_PROPOSAL.md. Dùng ROOT_PROBES.json, EVENT_CALL_PATH_CONTROL.json, TERMINAL_CALLER_PROBE.json, CANDIDATE_IDENTITY.json, POST_REVIEW_HASH_CHECK.json, PROGRESS_AUDIT_20261019.json để định vị bằng chứng. 89/89 là worker claim; root không chạy broad89 khi micro còn fail. Không sửa evidence này.

Đọc MAIN/AGENTS.md, docs/pm/SESSION_PROTOCOL.md, CODEX_PM_HANDOFF.md và ROADMAP.md; chúng có historical overlays, không thay current-byte state. Binding product/technology scope ở:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/PROMPT_GEMINI_MOTIONFORGE_VI.md`.
Giữ Q01–Q12/T01–T15/source22:01/cast/audio/runtime pins và rootG1→G2→G3. Từ skills đã có chỉ nạp debugging, receiving-code-review, verification/context phù hợp; không nạp toàn kho hoặc toàn transcript.

Codex là final reviewer. Implementation owner được code/test trong allowlist. Manager/QA không sửa production; tự review không thay Codex. Packet này được user chuyển cho exact owner mới kích hoạt correction; Codex không tự dispatch bạn từ cuộc review.

## Preflight, owner và context

Model giữ `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1`, existing high route/reasoning; fallback OFF. Không đổi model/account/globalrouter. `gemini-implementation-owner` chỉ là label, không dùng làm resume ID.

Audit actual native turn/process PID+creation-time, children, queue/lease/controller; latest root snapshot19/10 cóqueue0/0, watchdog26068/50164, turn09:30stop. Đây không thay preflight lúc bạn nhận prompt. Không thêm một resume song song vì daemon còn sống; reconcile ownwatchdog trước. Không kill đại trà hoặc xóa lock. Unknownowner/children phải giải quyết trước production write.

Audit context health: nhận đúng5closed/15open và root repro thay vì lặp lại20/20PASS. Dùng compact checkpoint, mỗi phase một outcome và sourcehash; không tạo writer thay thế chỉ vì context dài. Nếu context hỏng lặp lại hoặc destructive incident, báo evidence để Codex quyết định transfer; chưa có quyền mở writer khác.

Pin gitHEAD/branch/dirty attribution ở MAIN và INTEGRATION bằng đọc; không commit/push/reset/clean/stash/restore. Snapshot byte-for-byte + SHA256/size/lines/mtime writable/protected files, verify snapshot trước patch. Candidate01/02/rootpackets/media cũ frozen. Existing source/test chỉ boundedpatch exactpreimage, kiểm shrink sau mỗi patch. Missing/destructive shrink→freeze, không reconstruct bằng memory.

## Allowlist và resource

R6 = `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6`.
EX = `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution`.

- Writable R6/scripts/r6_cache.py, r6_cotracker.py, r6_propagate.py, r6_ledger.py, r6_gate.py, r6_matrix.py.
- Conditional actual caller/producer fix: r6_key_recipe.py, r6_keygen_asset.py, r6_assemble.py; chứng minh need+preimage trước patch. Không mở refactor ngoài acceptance.
- Cho phép new small R6/scripts/r6_event_contract.py và r6_evidence_contract.py nếu dùng để thay parser/evidence heuristics bằng contract chung; không tạo framework/engine mới.
- Tests R6/tests/test_g1_r1_*.py; existing tests chỉ bổ sung/correct để assert contract thật, không weaken/delete/rename-to-hide failures. Không chạy broad legacy discovery trên live tree.
- New fixture/submission adapter/proof/checkpoint ở EX/G1-R1/continuations/<unique-id>/; packet mới EX/submissions/g1-candidate-03 hoặc unusedID, không ghi đè01/02.
- Current EX/STATE.json/CHECKPOINT.json/RESUME.md được patch sau preimages; record actual changedfiles/openrows/owner/nextcommand.
- Coordination-only patch EX/auto_nudge_watchdog.py và EX/telegram_heartbeat.py để pending review không model-nudge và không lấy self-touch làm progress. Snapshot trước, audit ownprocess lifecycle khi áp dụng. Không tự mở recurring schedule mới, không sửa globals.

Protected: MAIN/INTEGRATION/prodDB/HermesDB/router/runtime/weights/source/CAST/R4R5/vendor/historical receipts/terminal writers và controller production. Database chỉ read-only. Current historical write_terminal_record_r6g.py không mở sửa; tạo current adapter mới ởEX, bind đúng dependencies, giữoldconsumer làm negativecontrol.

Maximum1productionwriter; GPU0/no new inference/render. Optional1–2 read-onlyQAchildren nếu toolnative khả dụng, ID/status/output thật, fixture disjoint. Same effective model route; quota block không fallback hay tạo task để né. Nếu delegation unavailable thì ghi thật và tiếp tục phần có thể làm.

## Thực hiện theo nhóm, không chỉ trả lại kế hoạch

1. **R01 — reference và graph:** `wrong_invocation/fake_grey.png` và graph thiếu R1 hiện vẫn được chấp nhận. Tái dùng validator file/hash/recipe, kiểm đúng mapping consumed → upload → node input. Giữ các controls thiếu/null/sai role/sai path/sampler. Kiểm actual run_key → deps → reuse/gate, cả trường hợp sai lẫn restyle/black/replay hợp lệ.
2. **R03/R05 — thời gian:** dùng một parser chung cho f zero-based và frame one-based, strict integer, conflict, bounds và contact windows. Actual tracker CLI phải giữ frame43 thành43; f700 trong clip50frame phải bị từ chối. Window thiếu coverage/không có visible pair phải UNKNOWN/FAIL; không clamp dữ liệu sai thành thành công. Kiểm tensors, queries và identity của source/output. Giữ transition20/50 đã chứng minh. Với cuts, chứng minh source shot plan đã chia mỗi cut thành boundary và từ chối dữ liệu vi phạm, hoặc truyền canonical cut contract vào planner thật; không tự đoán schema mới.
3. **R04 — propagation:** kiểm exact names/count/frame identity/invocation/decode trước publish. Child rc7, partial, corrupt, extra, wrong names và stale retry phải làm parent nonzero, ghi failure receipt và không để stale success manifest được dùng. Một failure boundary phải bao phủ staging, child, merge, decode và finalize. Giữ failed bytes. Dùng các real CPU child fixtures của root và valid control; không mock run_one để claim child process thật.
4. **R06/R07 — evidence và publication:** bỏ PASS dựa vào file length, kind string hoặc thiếu receipt. Tái dùng verify_deps và semantic review validators; evidence phải có current hash/input/invocation/coverage. Decode ảnh/container theo mục đích kiểm. Tạo một current submission adapter kiểm toàn bộ record/artifacts trước atomic publication; failure phải nonzero và không xuất TASK_SUBMITTED. Manifest/terminal cùng namespace và identity, có required artifact set, thứ tự hash không tự tham chiếu, mutation sau freeze phải bị từ chối. Historical writer clone là negative control, không sửa file lịch sử. Matrix main hiện không truyền artifacts ở final mode: sửa contract nối caller thật. Giữ C01 pre-encoder gate và encoder spy tests.
5. **R08 — concurrency evidence:** ba production hashes khớp proof34/34. Đối chiếu source/runtime/test/raw outcomes và các lifecycle cases từ proof51/51 trước khi dùng VERIFIED_UNCHANGED. Toy os.open race không được tính là controller proof. Nếu thiếu, chỉ chạy các cases còn thiếu trong clone; không chạy historical script có hardcoded output/rmtree. Proof mới phải dùng actual contested operation, hai process sống, bounded joins, một winner/một child, toàn bộ ledger và đúng PID creation-time/UNKNOWN/detached semantics.
6. **R09 — state và liveness:** xuất closed/open rows từ assertions và raw receipts; không hardcode20PASS. Candidate phải mang exact source/support dependency snapshots và hashes để root tái hiện không phụ thuộc live bytes. Changed files/task/model/actualSID/checkpoint/resume phải nhất quán. Sau submit đặt WAITING_CODEX_REVIEW; daemon không gọi model chỉ để chạm mtime. Tách heartbeat activity khỏi productive progress. Không báo đang coding hoặc GPU chạy24/24 chỉ vì server online, VRAM rảnh hoặc timestamp mới.

## Nghiên cứu và lựa chọn kỹ thuật

Đọc bảng RESEARCH_DECISIONS_VI.md. Runtime đã có Pydantic2.13.5, FileLock4.0.1, Pillow12.3.0, ffprobe8.1.2. Ưu tiên các thành phần đó và validators hiện hữu. Thay heuristic bằng schema và domain contract; chưa có bằng chứng cần thay video engine vì lỗi parser/evidence. Không cài cả shortlist.

Nếu đề xuất upstream khác, ghi nguồn official/GitHub, ngày kiểm, version/commit, license, compatibility Windows/Python/Torch/CUDA/GPU, chi phí chuyển đổi và so sánh trên cùng fixture/source unit. Chưa adopted/wired/proven phải ghi PROPOSED. README/demo/stars không là bằng chứng chấp nhận.

Với từng finding ghi symptom → actual call path → root cause → vì sao test bỏ sót → PATCH/REUSE_INSTALLED/ADOPT_UPSTREAM/REPLACE/DEFER_WITH_REASON. M07 chép lại thuật toán trong test, M08 mock child, M14/M16 chỉ gọi helper, M18 toy lock, M20 chỉ kiểm owner là những khoảng trống đã chỉ rõ. Không lặp cách test này để claim closure.

## Verification, checkpoint và điểm dừng

Chạy micro repro → đủ20 rows có subcase evidence → focused/static actual callers → final relevant suite89 và tests mới. Giữ5 rows đã verified nếu dependency bytes không đổi; khi đổi, chạy lại phần ảnh hưởng. Không lặp suite/log/state mỗi heartbeat. Không dùng broad legacy discovery trên live tree.

Runtime: `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe -B`. C01_WORKER_DIR, C02A_WORKER_DIR, C02B1_WORKER_DIR, C02B2_WORKER_DIR và C02B3_WORKER_DIR đều trỏ sandbox mới. No GPU/external model calls cho CPU proof. Mỗi receipt có command/cwd/start/end/exit/runtime/source hashes/expected/observed. Lưu test node IDs và counts thật;20 matrix rows khác test count. Schema validation không thay semantic PASS.

Quota5h/tuần, workspace credits, auth và route404 phải ghi lỗi/reset thật, lưu checkpoint rồi báo đúng action cần thiết. Không mua/reset/fallback/tạo owner hoặc account khác để né quota. Không hứa tiếp tục chạy nền khi turn đã stop.

Checkpoint sau mỗi nhóm coherent, trước compaction và resume: landed delta, open rows, latest hashes, children và exact next command. Heartbeat20phút khi task thực sự active;8phút không có tiến triển thì audit. Khi WAITING_CODEX_REVIEW không resume model hoặc lặp heartbeat để tiêu quota. Không đặt thêm trần tổng budget; tiếp tục trong scope tới acceptance, blocker thật hoặc user stop.

Sau khi writer/QA terminal, freeze exact bytes, finalize evidence/manifest rồi post-hash check. Nộp REPORT_VI, MANIFEST, source/dependency bytes, DIFF, raw TEST_RESULTS, matrix20rows, SELF_REVIEW, STATE snapshot, CHECKPOINT, RESUME, LIVE_JOBS và bảng root cause/reuse decisions. Dùng candidate03 hoặc ID chưa tồn tại; giữ01/02. Còn row thiếu thì ghi đúng, không claim all PASS.

Trạng thái submission: `SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối`. Dừng chờ Codex; chưa mở media/full source/tool integration.

Bắt đầu preflight và thực hiện các nhóm trên ngay khi user giao prompt vào exact session. Chỉ report candidate đủ review hoặc blocker thật; không dừng sau kế hoạch hay mỗi helper.
