**Đã bổ sung quy tắc review thường trực tại canonical rules §10.1 — 18/10/2026.**

Mỗi review phải giải thích nguyên nhân, vì sao test cũ bỏ sót, nghiên cứu phương án sẵn có và chốt sửa/tái dùng/thay thế bằng bằng chứng. Đây là research addendum cho G1; verdict CHANGES_REQUESTED và packet candidate01 giữ nguyên. Chưa cài dependency, thay code hoặc chạy inference trong lượt này.

**Chẩn đoán lại G1 và lựa chọn sơ bộ**

| Finding | Nguyên nhân và vì sao lọt test | Phương án sẵn có | Quyết định cho lượt sửa |
|---|---|---|---|
| R01: thiếu grey_ref/sai sampler vẫn hợp lệ | Dependency validator viết tay bỏ kiểm trường bắt buộc theo mode và không so sampler; tests thiếu biến thể record sai nhưng đã tính lại hash | Pydantic strict schema + validator liên trường, trên thư viện đã cài | REUSE_INSTALLED cho cấu trúc record; PATCH phần đối chiếu graph/input/hash. Giữ duplicate-key parser và semantic checks. Chưa có proof implementation mới. |
| R02: CLI thiếu argparse | Patch xóa import; tests import helper thay vì chạy CLI | Ruff F821 phát hiện undefined names; argparse đã có trong Python | PATCH import/entry point; đề xuất ADOPT_UPSTREAM cho focused lint gate nếu có runtime phù hợp. Không có lý do thay tracker vì lỗi CLI. |
| R03: tensor rỗng/visibility NaN vẫn nhận | Wrapper chỉ kiểm shape và tracks, chưa kiểm coverage/visibility; tests chỉ có vài negative cases | CoTrackerPredictor chính thức và tests của upstream; NumPy hiện có | REUSE_INSTALLED/ADOPT_UPSTREAM contract của đúng phiên bản đang pin, thay phần adapter đọc sai nếu cần. Không thay tracking core khi chưa chứng minh core gây lỗi. |
| R04: child rc7 nhưng parent rc0 | main bắt SystemExit rồi print; tests dừng ở run_shot | subprocess.run(check=True), check_returncode hoặc propagation return-code chuẩn của Python | PATCH wrapper dùng primitive chuẩn và durable failure receipt. Không thêm workflow engine để giải quyết lỗi truyền exit code. |
| R05: bỏ exit/occlusion/release | Logic lấy mốc bị lặp ở ledger/gate/propagate; chỉ chọn visibility dương; tests không đi hết call path | Ledger/cut map hiện có là dữ liệu thẩm quyền; chưa xác minh upstream nào chuyển đúng schema riêng này | PATCH một adapter chuẩn hóa timeline dùng chung, có consumer tests. DEFER thay thuật toán timeline đến khi có ứng viên chứng minh bảo toàn frame map/contact; không bịa repo thay thế phù hợp. |
| R06/R07/R09: PASS rỗng, manifest/state sai | Đồng nhất file tồn tại/enum với bằng chứng, lọc absolute path theo substring, state copy lại dữ liệu cũ | Pydantic strict models cho record/mode; pathlib/hashlib có sẵn; artifact binding đã được C01 duyệt | REUSE_INSTALLED cho schema; PATCH actual evidence consumers và relative-path inventory. Pydantic không biết video đúng vai hay manifest có đủ coverage nếu chưa viết domain checks. |
| R08: race test không kiểm controller | Hai thread thử os.open; production dùng FileLock và lease lifecycle nên test sai tầng | filelock hiện có; actual dispatch/lease harness và historical proof có nguồn/hash | REUSE_INSTALLED, kiểm lại actual consumers trong sandbox. Không tạo mutex mới và không coi filelock tự giải quyết detached GPU lease. |

Các lựa chọn trên là quyết định kỹ thuật sơ bộ từ source/probes, chưa phải benchmark chứng minh đã tích hợp. Những lỗi G1 đã chứng minh tập trung ở adapter, contract, actual caller và evidence. Chưa có căn cứ từ review này để kết luận phải thay model/renderer của sản phẩm.

**Nguồn đã đối chiếu**

1. [Pydantic repository](https://github.com/pydantic/pydantic) và [strict mode chính thức](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/): hỗ trợ kiểm dữ liệu theo kiểu và bật strict validation. Repo công bố MIT. Runtime video14b đang có Pydantic **2.13.5**; cần pin đúng bản này khi thử, không tự nâng phiên bản. Strict mode có khác biệt giữa Python input và JSON; phải giữ kiểm duplicate keys/nonfinite, invariant domain và hash binding riêng.
2. [Ruff repository](https://github.com/astral-sh/ruff) và [rule F821](https://docs.astral.sh/ruff/rules/undefined-name/): rule phát hiện sử dụng tên chưa khai báo, phù hợp lỗi argparse. Chưa thấy distribution Ruff trong venv video14b; không kết luận các runtime khác cũng thiếu. Chưa cài/chạy Ruff; nếu chọn tích hợp phải khóa release/commit và kiểm license/compatibility bản cụ thể.
3. [CoTracker repository](https://github.com/facebookresearch/co-tracker) và [predictor source](https://github.com/facebookresearch/co-tracker/blob/main/cotracker/predictor.py): nguồn tham khảo actual query shape/transform/visibility, để đối chiếu với vendor local đã pin trước khi sửa. Link main là nguồn khảo sát, chưa là pin để triển khai. README nêu phần lớn dự án theo CC-BY-NC và một số phần có giấy phép riêng; reuse cho sản phẩm phải đối chiếu đúng code/weights và mục đích sử dụng, không mặc định clearance thương mại từ việc repo công khai.
4. [filelock repository](https://github.com/tox-dev/filelock): khóa file đa nền tảng; repo công bố MIT. Runtime video14b có **4.0.1**, production harness hiện đã dùng FileLock. Giữ primitive này và kiểm call path thật; license/compatibility không thay proof race/lifecycle.
5. [Python subprocess documentation](https://docs.python.org/3.11/library/subprocess.html): có cơ chế kiểm exit code và ném CalledProcessError khi check=True. Đây là thư viện chuẩn có sẵn, không cần thêm một dependency orchestration.

Ngày kiểm tra: 18/10/2026. Metadata local đọc bằng importlib.metadata, không cài/gỡ/update package. Các phiên bản CoTracker/Ruff chưa khóa cho thay đổi mới nên trạng thái **PROPOSED/UNVERIFIED**, không ghi “đã áp dụng”.

**Cách nghiệm thu phương án thay thế**

Dùng cùng fixture, cùng input bytes và cùng acceptance với baseline; đo negative controls, regression và chi phí runtime. Nếu lỗi nằm ở adapter, thay adapter đủ nhỏ; nếu có bằng chứng thuật toán/model không đáp ứng, nghiên cứu và thử upstream thay thế trên unit đã được cấp quyền. Không chọn giải pháp chỉ từ stars, mô tả quảng cáo hoặc vì đã tốn nhiều lượt sửa. Không render/cài toàn shortlist chỉ để hoàn tất research checklist.

Prompt G1 phiên bản mới trong cùng thư mục bổ sung bước này trước implementation; giữ nguyên 20 hàng acceptance và các quyền đã mở. Không dispatch từ tài liệu này.
