# MotionForge2D candidate03 — independent G1 review, 19/10/2026

**Verdict: CHANGES_REQUESTED. G1 chưa APPROVED; Gói B Media chưa mở.** G2/G3 và sản phẩm cuối vẫn chưa nghiệm thu. Report “89/89 PASS, 20/20 closure” không đủ và không khớp kết quả tái hiện độc lập.

Có tiến bộ thật: kiểm graph grey reference chặt hơn; frame43 giữ đúng43, f700 bị chặn; window không thấy điểm trả null thay NaN; wrong/extra frame bị chặn; đường pending review đã tránh model nudge. Root xác minh8/20 acceptance rows so với5/20 ở candidate02. Đây là tỷ lệ closure engineering, **không phải phần trăm hoàn thành sản phẩm**. Có regression: child hợp lệ hiện không render xong vì thiếu import và sai quy ước tên frame.

## Identity, scope và trạng thái thực

-17/17 manifest file hashes khớp actual bytes, đã snapshot độc lập và post-check17/17. Có9 file mới/thay đổi so với candidate02; xem DELTA_VS_CANDIDATE02.json.
- Packet worker có12 support snapshots nhưng không có toàn bộ17 source/test snapshots và không bind12support/adapter vào manifest gốc. Root đã tự bảo toàn để review; không tính đó là worker hoàn tất M19. Ba test cũ và vendor được ghi rõ là observed dependencies.
- Actual owner `20261017_115944_b2a338`, route `ag/gemini-3.8-flash-high`; latest observed assistant stop khoảng10:26+07. Comfy queue0running/0pending lúc root snapshot. Điều này không phải render24/24.
- MAIN HEAD `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, dirty baseline được ghi trong CONTEXT_RECONCILIATION.json; INTEGRATION được kiểm bằng Git read-only. Root không sửa candidate production/tests, không render/inference GPU, không dispatch Hermes hoặc mở lịch mới.
- Adapter thực ở EX/G1-R1/r6_submission_adapter.py, ngoài directory continuation được prompt trước nêu. Chưa có bằng chứng sửa historical writer; cần khai báo đúng path/lineage và bind adapter trong packet tới. Không overwrite lịch sử để hợp thức hóa.

## Findings hữu hạn

Tất cả correction về MF-DEMO-LONG-01/G1-R1, exact owner trên. Dòng dưới trỏ frozen candidate trong thư mục candidate/task/corrections/identity/r6, adapter trong observed_execution/G1-R1. Không lẫn frozen code với live patch.

### G1-R04 [P1] Propagation chặn cả đầu vào hợp lệ và chưa bao phủ mọi lỗi

`r6_propagate.py:161`: Image chỉ import local trong stage_shot_assets; run_shot dùng biến chưa định nghĩa. Actual main→run_shot→run_one→CPU child hợp lệ trả parentexit1 với `name 'Image' is not defined`. Ruff0.16.0 cũng báo5locations F821 trong RUFF_F821.json. Childerrorrc7/wrong/extra được chặn, nhưng đó không chứng minh đường thành công.

`r6_propagate.py:154–167`: yêu cầu0001..expect cho mọi run. Upstream pinned VideoSequence dùng global frame ID. Với beg11/end21 upstream tạo0011..0020; candidate đòi0001..0010. Root kiểm API naming upstream thật và cô lập bug thứ hai bằng diagnostic injection Image, không sửa bytes candidate. Run thứ hai bị reject dù output đúng upstream.

`r6_propagate.py:110–137,216`: gate/planner ở ngoài failure boundary; stage_shot_assets ném SystemExit khi thiếu key, không bị except Exception bắt. Root preflightfail và stageSystemExit đều parent1 nhưng giữ STALE_SENTINEL manifest và không ghi failure receipt.

Evidence: ROOT_PROBES.json; PROPAGATE_valid.json; PROPAGATION_BOUNDARIES.json; EXTRA_PROBES.json/upstream_names. Test `test_m08_m09...` chỉ mock run_one rc7; không có valid child, non1beg, corrupt decode dù docstring nói có. Cần actual positive+negative caller, đúng frame contract, invalidate stale success từ mọi failure phase.

### G1-R06 [P1] Evidence vẫn chấp nhận nhãn tự khai và video giả

`r6_evidence_contract.py:37–48`: chỉ tìm `ftyp` trong64byte và size>=100000; expected_frames không được dùng. File `ftyp` +99996byte x được Q08PASS với receipt tự khai9000frames. ffprobe cùng file trảexit1; valid CPU3frame control trảexit0. Report nói “decode MP4” là sai.

`r6_matrix.py:52–59`: garbage chưa chạy trong testfile + all_passed:true/tests_run:1 được Q05PASS. `r6_gate.py:383–388` coi bản sao nhãn PASS củaQ05/Q07 là supporting proof; stage_and_publish_matrix nhận empty manifest vẫn publish engineering candidate. Q01 hiện kiểm ảnh decode + PASS/shots list, chưa bind image hash/source/invocation/coverage. Q07 chọn bất kỳ1trong10deps đầu tiên dưới shared work, chưa chứng minh current required coverage.

Evidence: delegated_audit/PROBE_RESULTS.json; EXTRA_PROBES.json. Test chỉ dùng empty/nonimage/missingproof, không thử forged receipt, stale valid media hoặc duplicated labels. Thay file-magic/size/label heuristics bằng ffprobe/decode và evidence schema+domain validators; schema không thay semantic review.

### G1-R07 [P1] Submission không xác minh hash; final caller không nối artifacts

`r6_submission_adapter.py:42,59–66`: engineering kiểm tồn tại/kích thước, không recompute SHA. ABCD→WXYZ cùng4bytes vẫn xuất TASK_SUBMITTED. Size5 negativecontrol bị chặn. Final gửi record không có artifacts trước khi đọc manifest: cùng5artifact kinds+hash mà direct gate nhận thì adapter reject `ARTIFACT_KIND master=None`.

`r6_matrix.py:131–136` và `r6_evidence_contract.py:106–123`: build_manifest trước publish matrix; manifest có thể giữ hash matrix cũ rồi matrix bị thay. Hai thao tác move riêng không tạo một transaction cho cả bộ artifact. build_manifest thiếu kind mapping cần cho final gate và quét cả lịch sửR6. Cần explicit current artifact set, thứ tự freeze rõ, manifest không tự tham chiếu, consumer cùng namespace và atomic commit marker sau validation.

Evidence: delegated_audit/PROBE_RESULTS.json (same-size mutation, valid direct-vs-adapter control, stale hash sau publish). Test M14/M16 chỉ gọi helper và lọc path; không chạy actual submission positive/negative. Giữ historical writer làm negativecontrol, không sửa lịch sử.

### G1-R03/R05 [P2] Time parser chưa strict; tensor/cut proof còn thiếu

`r6_event_contract.py:18–25`: int() chấp nhận43.9→43, true→1, chuỗi43→43; cặp f42.8/frame43.2 được coi khớp. Contact cũng coercion. Docstring “strict integer” và self-review vượt khả năng thực tế. Installed Pydantic StrictInt từ chối ba kiểu sai trên cùng fixture, nhận integer43.

Các cải thiện frame43/out-of-range/null được root xác minh qua actual trackerCLI với controlled predictor: invisible→null, good→0, offset10→10. Không phải media quality proof. M06 còn thiếu full tensor/query/canvas/paired input identity coverage. Actual cut caller truyền[] khi cut chỉ ở plan; candidate chưa chứng minh canonical source→ledger→caller có cut hoặc mọi shot đã atomic theo cut. Không tự coi schema rootspy là canonical; owner phải chứng minh một trong hai phương án theo acceptance cũ.

Evidence: ROOT_PROBES.json; EVENT_CONTROLS.json; EXTRA_PROBES.json. M07 test vẫn viết lại phép tính local thay consumer; M11 chỉ gọi plan_runs trực tiếp. Cần strictcontract chung và đúng producer/consumer path, không thêm parser thứ ba.

### G1-R08 [P2] Controller proof chưa đủ provenance

Ba production hashes vẫn khớp historical34/34. File51/51 có case results, nhưng candidate test chỉ assert passed==51; chưa bind đầy đủ harness source/runtime/raw/coverage theo current contract. Toy O_EXCL race không dùng controller dispatch/lease thật; join chưa chứng minh cả hai process terminal. Chưa chứng minh controller bị hỏng; đây là evidencegap M17/M18. Tái dùng historical coverage đúng hash; chỉ chạy missing subset trong clone nếu thực sự thiếu. Không rerun historical hardcoded writer/harness trên live.

Evidence: Q11_BINDING_AUDIT.json; tests/test_g1_r1_correction.py:423–480.

### G1-R09 [P2] Frozen packet và state còn tự mâu thuẫn

STATE đã WAITING_CODEX_REVIEW nhưng next_command/open_findings vẫn candidate02, g1_candidate vẫn01, verified_facts nói hoàn tất20/20; testsduration vẫn11.173s so với candidate03claim9.816s. Matrix worker ghi root_status CLOSED dù chưa root verdict. Telegram helper hardcode “20/20 closure”. M19/M20 test chỉ kiểm owner, không kiểm các mâu thuẫn đó.

Watchdog code mới skip nudge ở WAITING_CODEX_REVIEW là tiến bộ; active retry vẫn20s cho mọirc1/2, chưa phân loại quota/auth với lỗi kết nối theo rules. Không kích hoạt nudge để test. Cần state từ receipt có provenance và tests bằng injected clock/process/network; không gọi model/Telegram thật chỉ để chứng minh watchdog.

## Validation và giới hạn

Root31 micro probes; actual event/tracker controls; actual CPU child boundary probes; delegated exact-byte gate/adapter probes được root đọc đối chiếu; focused asset suite10/10 PASS.17/17 source bytes stable trước/sau. **Không chạy broad89 khi micro còn fail** theo canonical gate order;89/89 là submitted claim, không phải root-confirmed suite. Counts không thay20acceptance rows.

Hai agent read-only đã chạm usage limit; root dùng outputs hoàn thành và tiếp tục review, không mở agent/model khác để né quota. Không lượng hóa tiền/quota đã tốn từ daemon uptime. Các request vision là phép thử riêng córeceipt; không tính chúng là tiến độ video.

## Vision và bước tiếp

Gemini qua9router nhận ảnh thật: direct7/7 và helper7/7, HTTP200. Đã tạo `vision/motionforge_vision_qc.py`, no fallback/no automatic retry, có hash ảnh và JSON issues để owner dùng. Native Hermes vision_analyze envelope tạo được trongprocess cô lập nhưng livecall timeout90s; không áp global capability override và không claim nativevideo/audio chạy được. Config hash không đổi. Xem vision/README_VI.md và VERIFICATION.json.

Prompt chính thức tiếp theo ở PROMPT_GUI_GEMINI_VI.md: sửa các failure trên cùng owner, self-review thực rồi nộp candidate04; B pilot chỉ activate sau root G1 approval. Kế hoạch video đã ghi rõ output300s/comparison/vision QC/rerun affected shots/G2; full source/app chỉ sau G2. Chưa có cơ sở hứa ngày hoàn tất khi positive render path và gate còn lỗi. Completion phải được đo bằng playable output và product workflow, không uptime hoặc số report.
