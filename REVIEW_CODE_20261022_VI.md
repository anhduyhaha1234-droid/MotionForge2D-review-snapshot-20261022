# MotionForge2D — báo cáo độc lập để review code và tiếp quản

**Mốc kiểm:** 22/10/2026 (UTC+7). **Kết luận:** dự án có nền tảng backend, frontend, workflow và một số render thử thật, nhưng **chưa có video 5 phút mới được nghiệm thu** và **chưa thể coi công cụ hoàn thiện**. `G1_APPROVED` chỉ áp dụng cho đúng bytes của candidate 16 và hợp đồng bằng chứng kỹ thuật; G2 media vẫn `BLOCKED/NOT_RUN`. Không suy ra phần trăm hoàn thành từ số module, test pass hay một file MP4 giải mã được.

## 1. Công cụ định làm gì

MotionForge2D là ứng dụng **local-first** để lấy video nguồn, phân cảnh và sự kiện, thay nhân vật/đạo cụ/artwork bằng một bộ tham chiếu mới, giữ câu chuyện, vai trò, hành động, tiếp xúc tay–vật, che khuất, camera, nhịp cắt và âm thanh gốc. Người dùng đích sẽ đi từ import → analyze → sửa role/scene → chọn và pin CAST version → duyệt ảnh neo → render theo cảnh → so nguồn/kết quả, sửa đúng cảnh lỗi → xuất MP4 và tái sử dụng CAST cho nhiều video. Agent cloud như Hermes/Gemini có thể lập kế hoạch và phân tích; phần sinh video dự kiến chạy local bằng GPU/ComfyUI để kiểm soát chi phí. Đây là **mục tiêu sản phẩm**, không phải danh sách tính năng đã nghiệm thu.

Pilot cần chứng minh là **300 giây / 9.000 frame ở 30 fps**, cắt từ video nguồn 22:01 tại `[2820,11820)`, qua 54 shot S0021–S0074. S0074 chỉ dùng 141 frame đầu. Quy trình phải chứng minh đúng nội dung từng sự kiện và file cuối nghe/xem được, không chỉ đúng số frame.

## 2. Phạm vi mã nguồn và độ tin cậy của snapshot

Repo private này bắt đầu từ bản bàn giao private 19/10, rồi cập nhật `project/` bằng ba file mới hơn ở working tree: [rules Hermes](project/docs/pm/HERMES_AUTOPILOT_RULES.md), [skills autopilot](project/docs/pm/AUTOPILOT_SKILLS.md), [G1 submission guard](project/docs/pm/tools/g1_submission_guard.py). Đối chiếu **trong phạm vi tập source được đóng gói**, có lọc `.env`, cache, log và output sinh tự động: 620 file local so với 619 file ở snapshot private cũ; **hai file khác bytes, một file chỉ có ở local, không có file chỉ có ở private**. `project/` là **tập nguồn chọn lọc từ nhánh master/working tree cũ**, không phải toàn bộ code app tích hợp. Bản đầy đủ 02/10 được đưa lên **nhánh `review/20261002-full-code` của repo private mới** với commit `f3917d1`; hai cây phải review riêng, không gộp thành một candidate. [Manifest snapshot](updates/20261022/SNAPSHOT_MANIFEST.json) ghi size/SHA-256 của 627 file `project/`, 113 file packet/log bổ sung và hai tài liệu đầu repo; manifest là chỉ mục, không tự là chứng nhận tính đúng của code.

Lịch sử Git của source còn nằm trong `source-history.bundle`. [Repo public cũ](https://github.com/anhduyhaha1234-droid/MotionForge2D) **vẫn public và không được sửa**. Default `main` public (`ee10e55`, 23/08) cũ hơn [nhánh full-code private mới](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/tree/review/20261002-full-code) (`f3917d1`, 02/10). Nhánh full-code là nguồn đối chiếu kiến trúc và tài liệu, **không** phải bản G1/G2 mới nhất. Mã nguồn đang làm trên máy gốc ở `master@a40e368` có thay đổi chưa commit; việc đóng gói sang repo này không reset hoặc chỉnh working tree gốc.

Snapshot đã chọn không chứa video nguồn 36.971.916 byte, model weights, virtualenv, output render và dữ liệu cá nhân lớn. Bộ ZIP dữ liệu lớn của bản bàn giao 19/10 vẫn nằm ở [Release của repo private cũ](https://github.com/anhduyhaha1234-droid/MotionForge2D-handoff-20261019/releases/tag/v2026-10-19-portable), không được nhân đôi vào repo review mới; xem `ASSET_RELEASE_MANIFEST.json` để kiểm hash. Video nguồn đã được tìm lại và xác minh SHA-256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`, H.264/AAC, 640×360, 30 fps, 1321,215420 giây; người tiếp quản phải cung cấp lại đúng bytes hoặc thiết lập pin nguồn mới. Các đường dẫn tuyệt đối trong receipt là provenance của máy cũ, không phải đường dẫn portable.

## 3. Cấu trúc và lõi công nghệ

| Phần | Code chính | Vai trò và mức đã chứng minh |
|---|---|---|
| Backend/API | Nhánh full-code: `app/main.py`, `app/api/app.py`, `app/api/routes/` | FastAPI; có route cho project/video, CAST, apply, QC/export. Cần thử lại chuỗi public API end-to-end. |
| Dữ liệu và job | Nhánh full-code: `app/persistence/`, `app/workflow/`, `migrations/` | SQLAlchemy/SQLite/Alembic; job, attempt, lease, receipt, restart/reconcile có code. Chưa chứng minh toàn bộ lifecycle trên máy sạch. |
| Phân tích nguồn | Nhánh full-code: `app/services/` | Ingest, scene/timebase, role/source facts, shot plan, cache, audio, QC và export. Nhiều producer/consumer còn cần nối và đối chiếu actual bytes. |
| Local video engine | Nhánh full-code: `app/adapters/media_engine/comfy.py`, `scripts/` | Adapter tới `mf_comfy`/ComfyUI, graph và model local. Engine phụ thuộc runtime/model ngoài Git; có thử render lịch sử, chất lượng không đạt. |
| Giao diện | Nhánh full-code: `frontend/src/app/`, `frontend/src/features/`, `frontend/src/lib/` | Next.js/React/TypeScript, Zustand, TanStack Query, Konva; có trang project, character, import/analyze, apply/review/export. Chưa có browser E2E được nghiệm thu cho toàn hành trình. |
| Gate G1 mới | `updates/20261022/g1/c16/` | Frozen candidate độc lập với `project/`; siết Q05 test receipt và Q07 dependency cho 54 shot. Được duyệt **chỉ đúng manifest**. |
| G2 preflight | `updates/20261022/g2/` | Transport, checker chỉ đọc, vault khôi phục ba file lịch sử. Media generation chưa chạy. |

Dependency nền gồm Python 3.11, FastAPI, SQLAlchemy, OpenCV/PySceneDetect, FFmpeg, PyTorch CUDA; frontend Next.js 16/React 19. CAST/ảnh neo và các control được bind theo source facts; ComfyUI chạy graph cục bộ; output phải có artifact hash và QC gắn với đúng attempt. Kiến trúc này hợp lý về ranh giới trách nhiệm, nhưng còn khoảng cách lớn giữa **có module** và **người dùng thực sự đi trọn luồng**.

## 4. Đã làm được gì, bằng chứng nào

| Mốc | Bằng chứng kiểm độc lập | Điều không được suy diễn |
|---|---|---|
| Nền tảng source/UI/API | Source snapshot và nhánh full-code công khai; 4.191 test được pytest collect ở snapshot full-code 02/10. | Số test collect không chứng minh tất cả pass hoặc UX hoàn chỉnh. |
| R5/R6 render lịch sử | R6 có MP4 300s/9.000 frame giải mã được, audio đầu/giữa/cuối khớp; [review R6](review_and_handoff/motionforge-r6-checkpoint-review-20261014/REVIEW_VI.md) xem 54 midpoint + 23 frame bổ sung. | Hình R6 sai người/pose/contact ở nhiều shot; verdict `CHANGES_REQUESTED`, `QUALITY_ACCEPTED=0`. |
| G1 candidate 16 | [Root review](updates/20261022/g1/root_review.md), [guard](updates/20261022/g1/guard/VERIFICATION.json): 8 suite, 92/92 test, 116/116 subtest; [challenge](updates/20261022/g1/challenge/CHALLENGE_RESULTS.json): positive và 12 negative actual adapter→gate. Manifest SHA-256 `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`. | `G1_APPROVED` chỉ cho engineering evidence Q05/Q07 và quyền chuẩn bị G2; không chứng nhận media. |
| G2 transport | [Root review](updates/20261022/g2/ROOT_REVIEW_G2P01.md) kiểm source pin, bản sao C16/pilot, 8 negative path/hash. | Chỉ là copy/transport an toàn; không render. |
| G2 readiness | [Checker](updates/20261022/g2/preflight/readiness.py), [READINESS](updates/20261022/g2/preflight/READINESS.json), root chạy lại 9/9 test: 51 check = 19 PASS, 25 FAIL, 7 UNKNOWN, kết quả `BLOCKED`. | GPU/ComfyUI/model chưa được chạy hoặc chứng minh loadability. |
| G2 recovery | [Vault](updates/20261022/g2/recovery/vault-g2b2-001/), [receipt](updates/20261022/g2/recovery/RECEIPT.json), root chạy lại 6/6 test: khôi phục exact ledger, CAST atlas và graph template; 25 PASS, 1 UNVERIFIED. | Không khôi phục được 14 PNG CAST, storyboard đầy đủ hay working runtime. |

### Kiểm thử thực hiện để viết báo cáo này

- `git`/file inventory và SHA-256 trên source, candidate và các receipt. Ba file source cập nhật đã đối chiếu byte sau copy.
- `pytest --collect-only -q tests` trên code full-code 02/10: **4.191 tests collected**, exit 0. Lần CPU chạy từ ZIP thiếu `.git` gặp failure đầu tiên do test gọi `git show`; trên **Git checkout thật** của cùng commit, module liên quan đạt **28/28 PASS**. Toàn suite chưa chạy xong trên checkout thật. Chi tiết và log ở [phiếu kiểm thử](updates/20261022/TEST_AUDIT_VI.md). Không đánh đồng các test này với G1 C16 hoặc chất lượng media.
- C16 và G2 có các root-review riêng nêu trên; các test đó xác minh hợp đồng/diagnostic, không phải kiểm định chất lượng video.

## 5. Vì sao liên tục báo xong nhưng sản phẩm chưa xong

1. **Sai hợp đồng hình ảnh trước khi đến model.** Harness R5 gán prompt BOOK cho các shot khác loại, cho phép anchor chưa duyệt và dùng mask/pose fixture. Cảnh giấy/zoom thành người đọc sách, cảnh ký giấy cũng sai nội dung. Khi source facts, CAST, anchor, control và graph không bind theo từng shot bằng bytes, model tốt hơn cũng không sửa được việc đầu vào sai.
2. **Event/contact không đi đến actual consumer.** R6 propagation lấy grid frame `1,11,21,…`, bỏ nhiều key off-grid như f103/f105/f107. CoTracker từng đọc sai schema `event_map.shots`, tạo `windows: []`; drift trung bình không phải chứng minh tay giữ vật. S33 thêm đầu lớn vào người trên giường, S61 còn mặt nguồn và portrait phía sau, S73 mất sổ/động tác cầm. Đây là lỗi production path và semantic validation, không chỉ là lỗi thẩm mỹ.
3. **Gate/caching từng tin metadata tự khai.** R6 assemble không gọi semantic gate; record trống có thể PASS, cache dựa mtime cho phép 9 frame cũ + 1 frame mới, dependency chưa khóa source/model bytes. G1 C16 đã sửa đúng một phần Q05/Q07 ở frozen engineering candidate và được challenge âm tính, nhưng cần chứng minh hợp đồng đó đi vào media pipeline thật, không chỉ copy code có test xanh.
4. **QC và export chưa đóng vòng.** Một số comparator tồn tại mà production caller chưa được thấy; zero QC item không phải video đúng. S12 export lịch sử render chunk nhưng fail `av_policy`; chưa có file cuối accepted/reopen trên app. UI vẫn thiếu bằng chứng browser E2E import→CAST→anchor→render→QC→retry→export; batch render và cài sạch chưa được chứng minh.
5. **Quản trị evidence và môi trường.** Candidate/receipt trước đây từng tự khai PASS hoặc dùng đường dẫn/fixture cũ; chạy agent nhiều vòng tạo báo cáo nhanh mà không làm tăng chất lượng media. Chính vì vậy phải giữ manifest-exact, negative challenge, root review và tách “engineering approved” khỏi “media accepted”. Hiện G2 thiếu dữ liệu và runtime thực; đó là blocker xác minh được, không thể quy đơn giản là “Gemini kém”.
6. **Khả năng chuyển máy của script mới còn hạn chế.** B2 recovery test chạy lại trên bản sao ngày 22/10 được 4/6, vì script khóa hash của checkpoint trước khi root cập nhật trạng thái. Fail-closed này bảo vệ lineage nhưng buộc tạo phiên bản/receipt mới khi tiếp quản; không thể coi packet lịch sử là một installer chạy lại nguyên xi. [Log và giải thích](updates/20261022/TEST_AUDIT_VI.md).

## 6. Phần nào chưa hoàn thiện, điều kiện đóng cụ thể

| Ưu tiên | Khoảng trống hiện tại | Cách đóng có thể review |
|---|---|
| P0 | 14 PNG front/profile CAST trong atlas pin lịch sử: tìm 0/14 hash trong 37.776 PNG >1KB đọc được ở C:; fixture 15 byte không dùng được. | Tìm đúng bytes hoặc tạo CAST/reference mới và **repin có version/lineage**, duyệt identity/đa góc; không gắn nhãn là CAST cũ. |
| P0 | Storyboard 54 shot và media inputs/output cho pilot chưa có; chỉ thấy fixture S0021. | Khôi phục/tạo storyboard nguồn theo exact span, source facts, role/event/contact và binding cho từng shot; kiểm completeness trước GPU. |
| P0 | Venv `video14b` lịch sử thiếu, R4 SAM2/R5 CoTracker dirs chưa đầy đủ; endpoint code 8188 khác launcher cũ 8210; queue/lease chưa xác nhận. | Pin environment/model/node API; cold-start smoke có receipt; reconcile lease/queue trước khi render; không dựa “weight có trên đĩa”. |
| P0 | G2 300s media `NOT_RUN`; R6 cũ 300s sai nội dung. | Pilot theo stage: vài shot khó có trước/contact/hold/release và hard cut, held-out visual review source/ref/final; sau đó đủ 9.000 frame, audio/export, QC và nghiệm thu người dùng. |
| P1 | G1 C16 frozen nằm tách `project/`; tích hợp vào app/worker chính chưa chứng minh. | Chỉ sau gate hợp lệ, cherry-pick/port contract vào consumer thật, chạy negative tests ở production path và source hash/manifest; không giả định repo snapshot là bản tích hợp. |
| P1 | Browser flow, anchor approval, actual observations/QC, audio S12, batch và clean-host package. | Một vertical slice qua UI/public API, no SQL seed; actual output observation fail-closed; S12 decoded/reopen; rồi hai video cùng cast và máy sạch. |

Trong bước kế tiếp, ưu tiên **khôi phục hoặc repin CAST + hoàn chỉnh storyboard + sửa runtime** trước GPU. Chạy vài shot đại diện để sửa đúng root cause của role/contact/occlusion; không render lại toàn bộ 300s chỉ để nhận thêm một file MP4 sai nội dung. Sau khi G2 có bằng chứng media, mới đánh giá UX, batch và phát hành.

## 7. Hướng dẫn cho reviewer bên ngoài

1. Đọc [README](README.md), [hướng dẫn cài lại](hướng%20dãn%20cài%20lại%20để%20chạy%20tiếp%20dự%20án.md), [rules canonical](project/docs/pm/HERMES_AUTOPILOT_RULES.md) và manifest snapshot. Phân biệt `project/` nguồn chọn lọc, nhánh full-code 02/10, với `updates/20261022/g1/c16/` frozen; không cộng test/approval của ba cây.
2. Bắt đầu từ [brief BA 29/09](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/blob/review/20261002-full-code/docs/external-review/PROJECT_BRIEF_VI.md), [known issues](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/blob/review/20261002-full-code/docs/external-review/KNOWN_ISSUES.md), nhánh full-code và [review R6](review_and_handoff/motionforge-r6-checkpoint-review-20261014/REVIEW_VI.md). Tài liệu cũ giữ nguyên mốc thời gian của nó; bản báo cáo này cập nhật G1/G2 đến 22/10.
3. Với mỗi claim, hỏi: exact bytes/commit nào, consumer thật nào, receipt process exit nào, negative case nào, và frame nguồn/ref/final nào. Xem trực tiếp lỗi S33/S61/S73 trước khi phê duyệt media. Đừng kết luận product pass từ pytest hay decoded MP4.
4. Review theo thứ tự: source/time map + per-shot bindings → anchor/CAST → event/contact/occlusion → actual producer/consumer/cache/gate → QC → S12/audio/UI E2E → batch/package. Ghi finding với expected/actual, path/line, reproduction và điều kiện đóng.

**Verdict bàn giao:** source/rules/evidence có thể tiếp quản; G1 candidate 16 engineering đã qua review độc lập; transport và preflight/recovery G2 có chứng cứ; **G2 media và sản phẩm vẫn chưa hoàn thành**. Repo private này là snapshot có bằng chứng để code reviewer bắt đầu, không phải release chạy được ngay.
