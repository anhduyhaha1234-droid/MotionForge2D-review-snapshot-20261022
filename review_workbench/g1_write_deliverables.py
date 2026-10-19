from pathlib import Path
import json, hashlib, datetime, difflib, shutil
BASE=Path('C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2')
OUT=BASE/'outputs/motionforge-g1-review-20261018'
EX=BASE/'outputs/motionforge-gemini-handoff-20261017/execution'
R6=Path('C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6')
MG=R6.parents[4]/'manager'
SNAP=OUT/'candidate/task/corrections/identity/r6'
def link(label,path,line=None): return f'[{label}]({Path(path).as_posix()}{":"+str(line) if line else ""})'
def src(name,line): return link(f'{name}:{line}',SNAP/name,line)
def ev(name): return link(name,OUT/name)
def write(name,text):
    p=OUT/name
    assert not p.exists(),str(p)
    p.write_text(text.strip()+'\n',encoding='utf-8')
identity=json.loads((OUT/'CANDIDATE_IDENTITY.json').read_text(encoding='utf-8'))
manifest_sha=hashlib.sha256((OUT/'submitted_packet/MANIFEST.json').read_bytes()).hexdigest()
gate_before=(SNAP/'scripts/r6_gate.py').read_text(encoding='utf-8').splitlines(True)
gate_after=(OUT/'observed_live/scripts/r6_gate.py').read_text(encoding='utf-8').splitlines(True)
write('POST_SUBMISSION_GATE_DIFF.patch',''.join(difflib.unified_diff(gate_before,gate_after,fromfile='G1_exact_candidate/r6_gate.py',tofile='observed_live/r6_gate.py')))

findings=[
dict(id='G1-R01',priority='P1',title='Asset provenance vẫn chấp nhận thiếu consumed input và graph sai sampler',
 locations=[('scripts/r6_cache.py',343),('scripts/r6_cache.py',365),('scripts/r6_cache.py',456)],
 actual='Bỏ consumed.grey_ref rồi tính lại self-digest: verify_deps trả (True, ok). Đổi SAMPLER của graph sang heun, cập nhật graph hash và self-digest trong khi recipe vẫn euler: verifier vẫn trả (True, ok). Control nguyên bản cũng PASS.',
 expected='Bản ghi incomplete hoặc graph không khớp effective recipe phải bị từ chối, kể cả hash/self-digest nhất quán. R1/R2 grey reference đang được graph tiêu thụ nên không được coi là optional.',
 impact='Claim Q07/T07 complete không đúng. Đây là bypass tại dependency verifier; probe không khẳng định đã vượt riêng semantic-review gate bằng một review cũ.',
 probes=['asset_valid_control','asset_missing_consumed_grey','asset_graph_sampler_differs_recipe'],rows='M01–M04',owner='Gemini implementation owner, task G1-R1 / A2'),
dict(id='G1-R02',priority='P1',title='CoTracker CLI crash trước khi chạy',locations=[('scripts/r6_cotracker.py',8),('scripts/r6_cotracker.py',198)],
 actual='Chạy đúng candidate bằng python -B r6_cotracker.py --help: exit 1, NameError: argparse is not defined. Diff A3 đã bỏ import argparse nhưng main vẫn sử dụng.',
 expected='CLI --help exit 0; entry point thực phải hoạt động trước khi đóng T08.',impact='Không thể dùng CLI đã công bố để tạo paired tracking evidence.',probes=['cotracker_cli_help'],rows='M05',owner='Gemini implementation owner, task G1-R1 / A3'),
dict(id='G1-R03',priority='P1',title='Tracker validator nhận tensor rỗng và visibility không hợp lệ',locations=[('scripts/r6_cotracker.py',23),('scripts/r6_cotracker.py',128),('scripts/r6_cotracker.py',139)],
 actual='Các trường hợp T=N=0, visibility toàn NaN, visibility toàn 9 đều trả (True, ok). Validator chỉ xét shape và finiteness của tracks. Reader dùng both.any() của toàn clip khi tính metric từng window; chưa chứng minh window rỗng/query mismatch được chặn.',
 expected='Reject empty/nonfinite/out-of-contract tensors; kiểm tra coverage/visibility/query/frame identity ở actual reader, window không có mẫu hợp lệ phải UNKNOWN/FAIL và không xuất PASS/NaN JSON.',
 impact='T08 chưa đóng. Metric có thể được tạo từ dữ liệu không hợp lệ; probe này không phải đánh giá chất lượng video.',probes=['tracker_empty_tensors','tracker_nonfinite_visibility','tracker_invalid_visibility_range'],rows='M06–M07',owner='Gemini implementation owner, task G1-R1 / A3'),
dict(id='G1-R04',priority='P1',title='Propagation CLI nuốt lỗi child và trả exit 0',locations=[('scripts/r6_propagate.py',146),('scripts/r6_propagate.py',218)],
 actual='Probe CPU dùng run_one + run_shot + main thật, child thật sys.exit(7). Parent in PROPAGATE BLOCK ... rc=7 nhưng process exit 0 và trả về bình thường. main bắt SystemExit rồi chỉ print.',
 expected='Batch/CLI phải trả nonzero khi bất kỳ run bắt buộc thất bại, ghi durable failure và không publish success/cho dùng stale manifest. Test mock run_one hiện tại chỉ kiểm run_shot, bỏ sót main.',
 impact='Controller chỉ dựa exit code có thể coi job lỗi là thành công. Lỗi kế thừa chưa được đóng trong acceptance A3, không phải khẳng định mọi controller hiện tại đều chỉ dựa exit code.',
 probes=['propagate_cli_child_failure'],rows='M08–M09',owner='Gemini implementation owner, task G1-R1 / A3'),
dict(id='G1-R05',priority='P1',title='Event keys bỏ mốc occlusion/exit/release',locations=[('scripts/r6_propagate.py',32),('scripts/r6_gate.py',253),('scripts/r6_ledger.py',109)],
 actual='Fixture visible 1–19, occluded 20–29, visible 30–49, NOT_PRESENT từ 50, contact from=9/to=29: event_fids_for chỉ trả [10,30], thiếu chuyển trạng thái tại 20 và 50. Ba nơi ledger/gate/propagate lặp logic chỉ lấy window đầu VISIBLE/PARTIALLY_VISIBLE và contact.from.',
 expected='Chuẩn hóa duy nhất hợp đồng frame index; mang đủ entry/exit/occlusion/contact-end vào storyboard, key generation và gate; reject mâu thuẫn f/frame hoặc out-of-range theo contract rõ ràng.',
 impact='Mốc mất/che actor có thể không có exact key, interpolation kéo actor hoặc prop qua chuyển trạng thái. Cut helper được test riêng chưa chứng minh caller không băng qua hard cut; cần control trên call path, không suy luận rằng mọi shot hiện tại chứa cut nội bộ.',
 probes=['entry_exit_occlusion_release_keys'],rows='M10–M11',owner='Gemini implementation owner, task G1-R1 / A3'),
dict(id='G1-R06',priority='P1',title='Q-matrix tạo PASS từ file rỗng; batch gate chỉ kiểm enum và chưa có caller',locations=[('scripts/r6_matrix.py',29),('scripts/r6_matrix.py',41),('scripts/r6_matrix.py',48),('scripts/r6_gate.py',371)],
 actual='Tạo strip/json/test/mp4 0 byte: Q01/Q05/Q08 đều PASS; Q07 PASS chỉ vì source có chuỗi r6_key_deps_v3. gate_batch_conformance nhận mode=finla với toàn FAIL vẫn True; mode=final toàn PASS nhưng không artifact cũng True. Tìm trong scripts không có caller của gate_batch_conformance ngoài definition; test gọi helper trực tiếp.',
 expected='Mỗi PASS dựa proof parse được, đúng inputs/hash/invocation/coverage và caller thật. Mode lạ phải block. Final gate không thay artifact/remaining-work gate bằng enum; phải nối đúng submit call path và không nới C01 assembler binding đã duyệt.',
 impact='A4 chưa đóng Q05/Q10. Tên helper có chữ gate và test xanh không tạo ra cổng nghiệm thu thực tế.',probes=['matrix_empty_artifacts','unknown_gate_mode','final_gate_no_artifacts'],rows='M12–M14',owner='Gemini implementation owner, task G1-R1 / A4'),
dict(id='G1-R07',priority='P1',title='Manifest bỏ toàn bộ cây R6 nằm dưới thư mục work',locations=[('scripts/r6_matrix.py',77),('scripts/r6_matrix.py',89)],
 actual='build_manifest loại mọi absolute path chứa /work/ hoặc \\work\\. R6 thật nằm dưới Documents/Codex/work. Fixture có file thường dưới work/manifest-root/r6 cho count=0. main vẫn ghi R6/R6G_MANIFEST.json thay vì namespace invocation.',
 expected='Lọc theo relative path và phạm vi evidence rõ ràng; manifest đủ file bắt buộc, cấm rỗng, bind đúng invocation. Record mới ghi vào namespace mới, không đè lịch sử; xử lý self-manifest hash theo thứ tự freeze rõ ràng.',
 impact='Q10 không có manifest đầy đủ; đổi mỗi NS header chưa thực hiện isolation đã claim.',probes=['manifest_work_parent'],rows='M15–M16',owner='Gemini implementation owner, task G1-R1 / A4'),
dict(id='G1-R08',priority='P2',title='Test mô phỏng không đủ để tự đóng Q11/T13',locations=[('tests/test_gemini_a4_evidence_conformance.py',106)],
 actual='Test dùng 2 thread gọi os.open(O_EXCL) trên file tạm; không gọi dispatch_long/acquire_controller_lock/lease, không child lifecycle/PID creation time; join không timeout. Historical 34/34 có thật và 3 production script hashes vẫn khớp, nhưng G1 không cung cấp đủ binding/closure mới; root không rerun suite đó trong lượt này.',
 expected='Ghi UNKNOWN cho phần chưa kiểm. Có thể dùng proof cũ nếu đối chiếu đúng contract/bytes và raw outcomes; nếu rerun, dùng actual consumers trong sandbox với 2 process barrier tại thao tác tranh chấp, 1 winner/child, bounded joins, ledger đầy đủ, detached/UNKNOWN/PID-reuse controls.',
 impact='Đây là thiếu bằng chứng và overclaim; không kết luận production mutex đang hỏng. Hàm production dùng FileLock và lease lifecycle, khác hẳn primitive mà test A4 kiểm.',probes=[],rows='M17–M18',owner='Gemini QA/evidence owner; production harness chỉ đọc, không tự patch ngoài scope'),
dict(id='G1-R09',priority='P2',title='Packet/state chưa đủ nhất quán để resume đúng candidate',locations=[],
 actual='13/14 live manifest files khớp; live r6_gate khác candidate. Root lấy được gate đúng hash từ A4 probe snapshot nên review vẫn thực hiện được. Execution STATE tự nhận B2/B1 completed nhưng còn next_command/allowlist/open_findings của A1; CHECKPOINT A4 giữ hash cũ. Claim 27 protected 0 drift không khớp: so baseline có 19 match, 8 khác (7 nằm trong candidate; write_reviews chỉ quan sát live, chưa thể gán thời điểm đổi).',
 expected='Giữ candidate01 immutable, giải trình before/after và authority từng thay đổi. Reconcile owner session thật 20261017_115944_b2a338; một checkpoint current-byte nhất quán, phân biệt G1 bytes với live/B1 media và self/root approval.',
 impact='Không dùng nhầm verdict G1 cho code sửa sau đó. Các thay đổi nằm trong scope A2/A3/A4 có thể hợp lệ; “0 drift” không phải cách giải trình. Không kết luận B1 không được user cho phép: có chỉ đạo user mới hơn yêu cầu chạy xuyên suốt; lượt này vẫn chỉ nghiệm thu G1 theo 0.12.',probes=[],rows='M19–M20',owner='Gemini current manager/implementation lineage; Codex chỉ ghi verdict, không sửa state thay owner')]
for f in findings:
    f['paths']=[dict(candidate_snapshot=str(SNAP/p),production_path=str(R6/p),line=l) for p,l in f.pop('locations')]

report=f'''**Verdict G1: CHANGES_REQUESTED — candidate `g1-candidate-01` chưa được duyệt.**

Đánh giá theo canonical rules §0.12 và acceptance A1–A4 trong prompt bàn giao. Có **7 finding P1 và 2 finding P2**. Không có approval GPU/pilot/full-source/app integration phát sinh từ verdict này. Không thay rules sang §0.13 trong lần review này.

Tôi đã chạy lại độc lập **76/76 test, exit 0**; unittest báo 8.435 giây, cả subprocess 10.235 giây. Kết quả Gemini nêu là có thật, nhưng test hiện có không phủ đủ lỗi bên dưới. Không có GPU inference, render video hoặc sửa production source/test trong review.

Candidate manifest SHA-256: `{manifest_sha}`. Root snapshot giữ đủ **14/14 hash** đã nộp và kiểm lại sau tests vẫn khớp. **13/14 live file** khớp lúc chụp; gate đã đổi. Gate candidate được phục hồi bằng bản sao byte-exact từ A4 probe, hash `944eea8b6a1624cbb2983495fba5d2ff00cccb23460843f67987155cf664c0a2`; live hash `2767895e5ca1705c1dcff40e281e237b9334df6f0451c81f674656e9c41f42cc`. Không chạy suite trên live gate rồi gọi đó là G1.

Các dependency ngoài 14-file manifest được chụp riêng theo thời điểm review, không tự coi là đã được manifest submission khóa. Xem {ev('CANDIDATE_IDENTITY.json')}, {ev('POST_TEST_HASH_CHECK.json')} và {ev('POST_SUBMISSION_GATE_DIFF.patch')}.

**Findings — ưu tiên sửa trước khi nộp lại**
'''
for f in findings:
    locations=', '.join(src(str(Path(x['candidate_snapshot']).relative_to(SNAP)),x['line']) for x in f['paths']) or ev('CONTEXT_RECONCILIATION.json')
    report+=f'''\n**{f['id']} [{f['priority']}] — {f['title']}**\n\nVị trí: {locations}.\n\nThực tế/repro: {f['actual']}\n\nKỳ vọng: {f['expected']}\n\nTác động: {f['impact']}\n\nOwner sửa: {f['owner']}. Acceptance: {f['rows']} trong correction matrix.\n'''
report+=f'''
**Kết luận theo batch và Q/T**

| Phần | Kết luận root |
|---|---|
| C01/C02A/C02B1 | 40 regression PASS; giữ các acceptance trước, không suy rộng thành approval cả batch |
| A1 | 14 test PASS; không phát hiện P1 mới trong phạm vi kiểm lần này; chưa cấp approval riêng cho mọi kết hợp |
| A2 | 10 test PASS nhưng R01 tái hiện bypass contract; cần sửa |
| A3 | 7 test PASS nhưng R02–R05 còn mở; cần sửa |
| A4 | 5 test PASS nhưng R06–R09 còn mở; cần sửa/reconcile |
| Q05 | Chưa đóng toàn bộ A4; C01 pre-encoder sub-contract vẫn có regression PASS |
| Q07 | Chưa đóng: asset verifier còn chấp nhận contract thiếu/sai |
| Q10 | Chưa đóng: manifest/state/claim không nhất quán |
| Q11 | UNKNOWN cho acceptance G1 hiện tại; không khẳng định mutex hỏng |
| Q01/Q02/Q03/Q04/Q06/Q08/Q09/Q12 | Không nâng verdict media từ batch CPU này; media mới chưa được root xem/đo |

Bằng chứng raw: {ev('ROOT_76_TESTS.json')}, {ev('ROOT_76_TESTS.log')}, {ev('ROOT_PROBES.json')}, {ev('COTRACKER_CLI.json')}, {ev('PROPAGATE_CHILD_FAILURE_CONFIRMED.json')}.

`ROOT_PROBES.json` giữ nguyên lượt đầu: probe propagation có child rc=2 do lỗi đường dẫn trong fixture, parent vẫn rc=0. Đã sửa **fixture của reviewer**, không sửa candidate, rồi tái hiện bằng child thật rc=7 trong `PROPAGATE_CHILD_FAILURE_CONFIRMED.json`; đây là receipt dùng cho R04. Những probe khác không bị ảnh hưởng. Các kiểm tra bổ sung là phép thử CPU có điều khiển; không giả làm evidence GPU hay visual QA.

Snapshot vận hành: MAIN HEAD `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, có dirty/untracked từ trước; INTEGRATION HEAD `a52fca897906fd61a088016dd802718fdf06d217`, clean. Queue 8188 running=0/pending=0, 18 lease RELEASED, controller.lock không tồn tại tại snapshot; last message owner thật kết thúc `finish_reason=stop`. Đây không phải cam kết rằng không thể có writer xuất hiện sau snapshot. Preflight mới vẫn cần trước resume; không khởi chạy agent/dispatch/monitor trong lần review này.

Nhánh media B1 mà STATE tự báo 9 shots/1945 frames không phải bằng chứng G2 đã đạt. Giữ nguyên artifacts để review sau; không xóa hay ghi lại lịch sử. Không đưa phần trăm tiến độ toàn sản phẩm từ số lượng tests.

**Bước tiếp theo**: {ev('CORRECTION_MATRIX.md')} → {ev('SESSION_OPENING_PROPOSAL.md')} → gửi {ev('PROMPT_SUA_G1_VI.md')} cho owner Gemini hiện tại. Prompt này là một gói sửa G1 trọn vẹn, tự test và self-review trước khi nộp candidate02. Yêu cầu chạy xuyên suốt sản phẩm trước đó không làm candidate01 tự được APPROVED; yêu cầu mới nhất của user là trả verdict G1 theo §0.12.
'''
write('REVIEW_VI.md',report)

rows=[
('M01','R01','test_asset_missing_ref_rejected','Xóa grey_ref / null / wrong role / wrong path; self-digest hợp lệ; từng trường hợp verifier từ chối.'),
('M02','R01','test_asset_effective_graph_mismatch','Sampler khác recipe; R1/R2 reference sai; graph hợp hash nhưng sai effective inputs: phải block.'),
('M03','R01','test_asset_actual_producer_consumer_contract','Actual run_key → deps → skip/key gate; graph mutation phải block trước publish. Không chỉ gọi helper.'),
('M04','R01','test_asset_controls_and_regressions','Restyle, black passthrough hợp lệ, unchanged replay không gọi thêm stage/upload/post; 14 A1 + 10 A2 + 40 regression giữ.'),
('M05','R02','test_cotracker_cli_help_and_fixture_entry','Subprocess --help exit0; actual CLI controlled predictor/CPU fixture đến validation; không inference GPU.'),
('M06','R03','test_cotracker_invalid_tensor_matrix','T/N=0, tracks NaN/Inf, vis NaN/Inf/invalid type/range, shape/query mismatch, out-of-canvas: không PASS. Valid bool/probability theo contract rõ ràng vẫn đúng.'),
('M07','R03','test_cotracker_window_coverage_controls','Window không có visible pair, empty/out-of-range event, f/frame mapping; valid/known-bad fixture phân biệt; JSON không NaN; source/output query/time identity khớp.'),
('M08','R04','test_propagate_cli_child_nonzero','Child process thật rc7 → parent nonzero, receipt failure, không success/publish/assemble. Control rc0 + đủ output vẫn thành công.'),
('M09','R04','test_propagate_partial_stale_retry','Missing/partial/corrupt/extra/wrong-name output và stale prior manifest/retry khác invocation: fail closed; stdout-only BLOCK không được coi là thành công.'),
('M10','R05','test_event_transition_end_to_end','Fixture off-grid entry/exit/occlusion/reappearance/contact end đi qua ledger → board → key discovery → gate/propagate; boundary 20/50 phải có exact key.'),
('M11','R05','test_event_bounds_and_cut_call_path','Conflict f/frame, 0/negative/out-of-range, final endpoint; actual shot-plan caller không interpolate qua hard cut; không lấy helper-only test làm closure.'),
('M12','R06','test_matrix_empty_stale_wrong_evidence','0-byte/malformed/stale/wrong hash/other invocation/missing coverage → UNKNOWN/FAIL; file tồn tại hoặc code substring không đủ PASS.'),
('M13','R06','test_batch_gate_strict_modes_and_evidence','Mode lạ/thiếu; final allPASS thiếu artifact; fake engineering PASS thiếu proof: block. Giữ phân biệt historical technical PASS với candidate hiện tại.'),
('M14','R06','test_submit_actual_caller_gate','Actual submission/assembler caller dùng gate trước publish/copy/encode; encoder-spy negative controls; giữ C01 positive. Không sửa historical writer/terminal để tạo caller giả.'),
('M15','R07','test_manifest_work_ancestor','Windows root chứa work vẫn liệt kê mandatory artifacts; chỉ loại đúng R6-relative work nếu contract yêu cầu. Không empty-success.'),
('M16','R07','test_manifest_namespace_and_finalization','Namespace unique; sentinel lịch sử bytes giữ; manifest đủ required hashes, không self-hash stale; artifact mutate sau freeze làm gate block.'),
('M17','R08','test_q11_existing_proof_binding','Đối chiếu source/runtime/test/raw evidence hashes với historical proof; claim chính xác coverage; không coi mock os.open là controller proof.'),
('M18','R08','test_q11_actual_race_and_lifecycle','Nếu cần rerun: 2 live process rendezvous ngay contested operation, 1 winner/1 child, bounded joins, full ledger; PID reuse/UNKNOWN/detached child giữ lease. Chạy cloned sandbox, không patch harness ngoài scope.'),
('M19','R09','test_candidate_identity_reconciliation','14 candidate hashes rõ; live drift và 8 protected differences giải trình từng file/thời điểm/scope; giữ snapshot01 và B1 evidence. Current deps mới được freeze/hash đầy đủ.'),
('M20','R09','test_resume_state_truth','STATE/CHECKPOINT/RESUME cùng task/hash/owner/next action; owner thật vs label; no stale A1 facts; rootG1 CHANGES_REQUESTED; live_jobs theo process/queue hiện tại.'),
]
matrix='''**Finite correction matrix — G1-R1, 20 hàng acceptance.**

Mỗi hàng có raw command, exit code, timing, source hashes, observed/expected và owner; tên test dưới đây là tên yêu cầu cho lượt sửa, không phải test root đã chạy. Không tính số hàng thành số test hoặc % hoàn thành sản phẩm. Từng biến thể phải có subcase receipt; không bỏ negative controls để làm xanh.

| Row | Finding | Test/receipt cần có | Điều kiện đóng |
|---|---|---|---|
'''
for r in rows: matrix+='| '+' | '.join(r)+' |\n'
matrix+='''
Thứ tự: micro repro → 20 hàng matrix có evidence (M18 chỉ có thể dùng VERIFIED_UNCHANGED nếu M17 chứng minh đầy đủ contract/bytes/raw outcomes; không N/A vì thiếu thời gian) → focused tests/static actual callers → cả 7 module của suite 76 và tests mới. Dừng mở rộng kiểm tra khi closure đủ, không render GPU để chứng minh parser. Giữ riêng self-review và root approval.

M01–M16: implementation owner sửa trong A2/A3/A4; M17–M18 QA proof, harness production read-only; M19–M20 manager evidence owner. Maximum concurrent production writer = 1.
'''
write('CORRECTION_MATRIX.md',matrix)

proposal=f'''**Session Opening Proposal — G1-R1; PREPARED, NOT DISPATCHED.**

- Decision: resume same task/lineage `MF-DEMO-LONG-01`, correction G1-R1 after `g1-candidate-01 CHANGES_REQUESTED`. Không restart A1 từ checkpoint015 hoặc khôi phục source cũ đè live.
- Current real Hermes session: `20261017_115944_b2a338`; `gemini-implementation-owner` là label. Old Sol/DeepSeek sessions không phải target. Fresh owner/context/liveness preflight phải xác minh trước ghi; snapshot reviewer chỉ để điều tra.
- Model: `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1`; no fallback. Reasoning giữ effective provider-supported config, không bịa gán GPT Max cho Gemini. Không đổi globals/router/account để né quota.
- Context health: stale checkpoint/overclaims đã được ghi R09. Đọc rules đầy đủ; nạp review + matrix + current packet và đúng 2–4 skills liên quan mỗi task. Checkpoint sau coherent unit. Nếu context audit không đạt, chỉ chuyển owner sau old writer/children terminal và receipt transfer thật, không tự tạo lineage thứ hai.
- Dependency: R01–R09 chưa đóng; candidate01 hash không đồng nhất live gate. Freeze/reconcile trước sửa. Không cần đợi user chọn implementation routine trong write-set đã mở.
- Maximum safe wave: 1 production writer; có thể 1–2 subagents chỉ đọc/QA trong sandbox riêng nếu runtime hỗ trợ, không cùng sửa tree. Manager giữ registry/evidence; không hai writer. GPU=0 cho correction engineering này.
- Exclusive production write-set: R6/scripts/r6_cache.py, r6_cotracker.py, r6_propagate.py, r6_ledger.py, r6_gate.py, r6_matrix.py; r6_key_recipe.py, r6_keygen_asset.py, r6_assemble.py chỉ khi actual repro/call path cần, preimage riêng trước patch. Test mới `R6/tests/test_g1_r1_*.py`; existing tests patch-only nếu bổ sung assertions, tuyệt đối không giảm/xóa checks. Một submission builder mới chỉ trong `execution/G1-R1/`.
- Evidence write-set: `execution/G1-R1/**`, checkpoint/state hiện hành sau snapshot và reconciliation; candidate02 mới. Candidate01/root review packet, old media/receipts/terminals/proofs read-only.
- Protected: MAIN/INTEGRATION source/DB, prior reviews, R4/R5, source/CAST, weights/runtime, controller harness/upstream vendor, production media, old test semantics. Không Git mutation, full-file replace, blanket cleanup hoặc inference/render.
- Self-review: implement → isolated real-consumer probes → 20-row matrix → regression → independent QA subagent nếu có → fix trong cùng scope → freeze candidate02 → report. QA tự duyệt không cấp Codex approval.
- Dispatch authority: user nhận prompt để gửi owner; Codex không dispatch hay restart schedule từ review này. Prompt này chỉ sửa G1 theo yêu cầu hiện tại §0.12; thay orchestration sang end-to-end là thay đổi tách biệt, không dùng để nâng verdict candidate01.

Prompt khớp proposal: {ev('PROMPT_SUA_G1_VI.md')}. Review và matrix là đầu vào bắt buộc.
'''
write('SESSION_OPENING_PROPOSAL.md',proposal)

prompt=f'''Đọc TOÀN BỘ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` trước mọi preflight hoặc ghi file. Đây là correction cho kết quả Codex review G1 theo §0.12, không phải approval G1/media/product.

Bạn là owner Gemini hiện tại của MotionForge2D. Tiếp tục same task `MF-DEMO-LONG-01`, nhánh sửa `G1-R1`, từ current-byte state có đối chiếu, không restart dự án. Codex trả `CHANGES_REQUESTED` cho `g1-candidate-01`: 76/76 test hiện có PASS nhưng còn 7 P1 + 2 P2. Hãy xử lý trọn gói findings, tự kiểm tra và self-review rồi mới nộp một candidate02; không báo hoàn tất sau mỗi helper hoặc chỉ vì test xanh.

**Các đường dẫn phải đọc**

- Review: `{OUT.as_posix()}/REVIEW_VI.md`
- Acceptance hữu hạn 20 hàng: `{OUT.as_posix()}/CORRECTION_MATRIX.md`
- Proposal khớp scope: `{OUT.as_posix()}/SESSION_OPENING_PROPOSAL.md`
- Source/hash identity và raw repro: `{OUT.as_posix()}/CANDIDATE_IDENTITY.json`, `ROOT_PROBES.json`, `PROPAGATE_CHILD_FAILURE_CONFIRMED.json`, `ROOT_76_TESTS.json`, `CONTEXT_RECONCILIATION.json` trong cùng thư mục review.
- Binding technical/product contract: `{(BASE/'outputs/motionforge-gemini-handoff-20261017/PROMPT_GEMINI_MOTIONFORGE_VI.md').as_posix()}`; giữ A1–A4, Q01–Q12/T01–T15 và source/cast/audio/runtime pins. Không dùng summary thay rules.
- MAIN AGENTS.md và docs/pm/SESSION_PROTOCOL.md; skills digest `{(BASE/'outputs/motionforge-codex-takeover-20261015/skills/ACTIVE_DIGEST_VI.md').as_posix()}`. Chọn đúng skills debugging, verification-before-completion, receiving-code-review, context-compression cho công việc hiện tại; không nạp lại toàn bộ kho.

**1. Xác minh đúng owner và bảo toàn hiện trạng**

Actual Hermes session đã đối chiếu là `20261017_115944_b2a338`. `gemini-implementation-owner` là label, không phải ID để --resume. Model giữ `ag/gemini-3.8-flash-high` qua 9router `http://127.0.0.1:20128/v1`, không fallback. Kiểm effective model cho child nếu delegate; không giả lập child bằng các đoạn văn có tên role.

Đọc native active-session status, process PID + creation time/executable, launcher/children, queue/lease/controller. Heartbeat PID, session chưa ended hoặc output cũ không chứng minh worker đang chạy. Snapshot Codex: queue trống,18 lease RELEASED, không controller.lock; đây không thay preflight lúc bạn bắt đầu. Nếu có owner khác ALIVE/UNKNOWN chưa reconcile, chưa mở writer thứ hai. Không kill đại trà hoặc xóa lock.

Chụp byte preimages + SHA256 + size + lines cho từng writable/protected file, git HEAD/dirty attribution; dùng write_set_guard hiện có. Giữ nguyên candidate01 và root packet. Live gate đã đổi hash sau submission; giữ cả hai và viết receipt giải trình before/after. Không copy snapshot Codex đè production gate. State đã ghi B2 nhưng còn facts/A1 hashes cũ: reconcile, giữ history, không giả làm chưa chạy B1. Media đã có được giữ `UNREVIEWED`, không lấy code approval thay media approval.

**2. Ownership, scope và subagents**

Maximum 1 production writer; được tạo 1–2 subagents read-only để kiểm call graph/negative cases/evidence trên workspace fixture riêng nếu native tool khả dụng. Phân công task rõ, nhận child ID/status thật, đợi terminal + evidence rồi tích hợp. Manager/QA không đồng thời sửa production. Nếu native delegation không có hoặc hết quota, ghi giới hạn thật và tiếp tục trong khả năng hiện có; không nói đã tạo agents khi chưa có tool result.

Production root duy nhất: `{R6.as_posix()}`.

Writable: `scripts/r6_cache.py`, `r6_cotracker.py`, `r6_propagate.py`, `r6_ledger.py`, `r6_gate.py`, `r6_matrix.py`. `r6_key_recipe.py`, `r6_keygen_asset.py`, `r6_assemble.py` chỉ sửa khi actual repro/caller yêu cầu, có preimage trước. Test mới `tests/test_g1_r1_*.py`; existing test chỉ patch bổ sung không làm yếu assertions. Submissions builder mới, fixture/proof scripts và receipts dưới `{(EX/'G1-R1').as_posix()}/`. State/checkpoint current chỉ cập nhật sau khi chụp bản cũ và đối chiếu thật.

MAIN/INTEGRATION/DB, R4/R5/upstream vendor, runtime/weights, source/CAST, historical media/receipts/terminals, controller production không mở ghi. Nếu phát hiện harness cần patch ngoài scope: nộp exact repro/path/dependency, giữ Q11 UNKNOWN. Không rewrite engine, Git commit/reset/stash/checkout/push, cài thêm framework hoặc sửa lịch sử để làm xanh.

**3. Đóng trọn findings, không chỉ sửa thông báo**

R01: Asset dependencies phải complete theo mode; mọi consumed reference bắt buộc được xác minh. Graph effective sampler/refs/settings phải khớp recipe, kể cả self-digest đã được tính lại. Chứng minh actual producer → dependency → skip/gate, có positive unchanged reuse và black mode. Root thấy thiếu grey_ref và graph heun/recipe euler đều bị chấp nhận.

R02: Sửa CLI CoTracker mất argparse; kiểm subprocess --help và entry point fixture thực, không chỉ import module.

R03: Strict tensor/time/query/canvas/visibility contracts; T/N rỗng, NaN/Inf, mismatch, window không visible pair phải UNKNOWN/FAIL. Không NaN JSON và không clamp dữ liệu sai thành thành công. Evidence source/output cùng frame/window/query identities. CPU fixtures không được ghi thành semantic/GPU PASS.

R04: Child nonzero/partial/stale/corrupt/wrong-run output phải làm parent CLI nonzero và failure receipt rõ. Chặn old manifest reuse/publish/assemble. Root đã chạy child thật rc7 mà parent rc0; sửa actual main/run path. Preserve run directories/evidence, không blanket delete để che lỗi.

R05: Một contract nhất quán cho f zero-based/frame one-based và contact/class windows. Mang đầy đủ entry/exit/occlusion/reappearance/release vào storyboard, key gen và gate. Fixture visible→occluded tại20 và visible→absent tại50 phải có exact keys. Chứng minh caller không nội suy qua cut; helper plan_runs đơn lẻ không đủ.

R06: Q rows chỉ PASS từ parsed current evidence có hash/input/invocation/coverage. File 0-byte hoặc string trong source không là proof. Mode lạ fail closed. Nối gate vào actual submission caller trước publish; giữ artifact/remaining-work validation và C01 assembler gates. Có negative known-bad/source-copy/wrong-role controls phù hợp; hash hợp lệ không tự là semantic pass.

R07: build_manifest không loại toàn bộ path vì ancestor Documents/Codex/work. Lọc relative đúng phạm vi, đủ required files, không empty-success. Namespace mới cho final manifest; historical sentinel giữ nguyên; freeze/hash theo thứ tự tránh stale/self-reference.

R08: Không dùng 2 thread os.open để claim production controller race. Historical Q11 proof 34/34 và 3 source hashes còn khớp; đối chiếu đầy đủ contract/raw evidence trước khi dùng VERIFIED_UNCHANGED. Nếu chưa đủ, replay actual production consumers trong sandbox: 2 process barrier ngay contested operation,1 winner/1 child, bounded join/all ledger rows, PID creation-time/UNKNOWN/detached lease. Không chạy trực tiếp script historical có hardcoded output path hoặc rmtree trên folder cũ; làm runner mới isolated, giữ production consumer bytes.

R09: Reconcile manifest/checkpoint/resume/registry/owner/changed-files. Claim “27 protected 0 drift” phải thay bằng đối chiếu từng file/scope: root thấy19 match/8 khác, không có nghĩa mọi khác biệt đều trái phép. Mọi con số test/PASS và trạng thái phải có raw receipt. Candidate02 chứa source snapshot/dependency hashes đủ để root tái hiện không phụ thuộc live bytes.

**4. Kiểm tra và quản lý context/quota**

Chạy micro repro trước, rồi đủ20 hàng matrix, focused tests/static actual callers, cuối cùng7 module của suite76 và tests mới. Dùng Python đã pin `{Path('C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe').as_posix()}` với -B; fixture root mới, các C01_WORKER_DIR/C02A_WORKER_DIR/C02B1_WORKER_DIR/C02B2_WORKER_DIR/C02B3_WORKER_DIR đều trỏ sandbox. Đừng chạy broad legacy discovery hoặc GPU để kiểm parser. Mọi log có command/cwd/start/end/exit/source hash.

Checkpoint sau mỗi nhóm coherent: task+owner/model, changed hashes, closed/open matrix rows, actual live children, exact next command, known limits. Mỗi task context chỉ giữ authority + packet hiện hành + facts cần dùng; không lặp toàn transcript hoặc load cả video. Trước compaction/handoff lưu trạng thái đủ resume. Không coi compaction thành permission đổi task/owner.

Khi tool trả quota5h/tuần/credits/auth/model404, lưu lỗi thật và reset_at nếu có. Usage còn không chứng minh credits đã hồi. Không mua/reset/fallback/tạo task hay đổi account để né block. Không tạo heartbeat/cron để báo đang chạy; status ACTIVE chỉ khi có live turn/process và evidence tiến triển. Nếu runtime thực dừng, nói đã dừng và gửi checkpoint + action cần thiết; không hứa chạy nền24/24.

Không cần báo cuối mỗi microtask. Tự sửa/tự review xuyên suốt correction G1-R1; chỉ report candidate02 hoàn chỉnh hoặc blocker thật cần user/authority. Self-review không thay root review. Lượt này không tự mở render mới/full-source/app integration vì đây là verdict/correction G1 theo §0.12; chỉ đạo workflow end-to-end không được biến thành G1 APPROVED giả.

**5. Nộp một packet mới đủ tái hiện**

Tạo `{(EX/'submissions/g1-candidate-02').as_posix()}`; nếu đã có thì dùng ID mới, không ghi đè. Packet gồm REPORT_VI, MANIFEST có exact source/dependencies/snapshots, DIFF, raw TEST_RESULTS, matrix20hàng, SELF_REVIEW với known gaps, CURRENT_STATE/CHECKPOINT/RESUME cùng hashes, LIVE_JOBS/PID/queue/lease và owner lineage, provenance source locks.

Writer/children terminal, không active lease, freeze final bytes rồi lập manifest sau final evidence. Chạy lại hash checks; mutation sau freeze bắt buộc candidate mới. Báo `SELF_VERIFIED_PENDING_CODEX_G1`, không ghi ROOT_APPROVED/QUALITY_ACCEPTED/COMPLETE dự án. Liệt kê rõ row nào chưa đủ; không hạ bar hay bỏ tests để được PASS. Trả đường dẫn packet cho user chuyển Codex kiểm duyệt độc lập.
'''
write('PROMPT_SUA_G1_VI.md',prompt)
verdict=dict(schema=1,reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='Codex independent root',gate='G1',rules='HERMES_AUTOPILOT_RULES.md section 0.12',authority_sha256=identity['authority_sha256'],candidate='g1-candidate-01',candidate_manifest_sha256=manifest_sha,verdict='CHANGES_REQUESTED',parent_status='NOT_APPROVED',independent_existing_suite=dict(tests=76,passed=76,exit_code=0),findings=findings,new_media_authorized_by_this_verdict=False,production_changes_by_reviewer=False,dispatch_performed=False,next_prompt=str(OUT/'PROMPT_SUA_G1_VI.md'))
write('VERDICT.json',json.dumps(verdict,ensure_ascii=False,indent=2))
shutil.copyfile(BASE/'work/g1_capture_context.py',OUT/'g1_capture_context.py')
print(json.dumps(dict(verdict=verdict['verdict'],p1=sum(f['priority']=='P1' for f in findings),p2=sum(f['priority']=='P2' for f in findings),matrix_rows=len(rows),report=str(OUT/'REVIEW_VI.md'),prompt=str(OUT/'PROMPT_SUA_G1_VI.md')),ensure_ascii=True))
