# Hướng dẫn cài lại để chạy tiếp dự án MotionForge2D

Ngày chụp: **19/10/2026**. Bản này dành cho Windows/PowerShell và một máy mới. Giữ repo GitHub ở chế độ **private** vì có dữ liệu dự án, video nguồn và lịch sử điều hành. Không cần mang token, tài khoản Antigravity hay database phiên Hermes/Codex sang máy mới; đăng nhập lại bằng chính tài khoản của bạn.

## 1. Trạng thái chính xác khi tạm dừng

- Canonical rules là `project/docs/pm/HERMES_AUTOPILOT_RULES.md`, nhất là §0.12, §8.2 và §10.1. File này phải được đọc **toàn bộ ở phiên làm việc mới** trước khi viết prompt/dispatch.
- Gemini owner `20261017_115944_b2a338`, model `ag/gemini-3.8-flash-high` qua 9router, đã nộp `review_and_handoff/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-04/`. Báo cáo tự nhận `89/89` test và `20/20` matrix, nhưng đây là **SELF_VERIFIED_PENDING_CODEX_G1**, chưa là root approval.
- Review candidate03 đã kết luận **CHANGES_REQUESTED**, xác minh `8/20` hàng; review candidate04 mới có snapshot/hash/diff ban đầu trong `review_and_handoff/motionforge-g1-review-04-20261019/`, **chưa có verdict**. Không suy `G1 APPROVED` từ số test hay chữ CLOSED trong matrix.
- Gói B (video pilot 300 giây), nguồn dài 22:01 và tích hợp app còn khóa cho đến các gate G1/G2 tương ứng. Master cũ là bằng chứng lịch sử, chưa đạt chất lượng nghiệm thu.
- Chưa có lịch tự động để dự án tiếp tục khi máy này tắt. Trên máy mới, tự mở một phiên reviewer với prompt ở cuối tài liệu. Không tự tạo writer thứ hai hoặc giả định session ID cũ chuyển máy được.

## 2. Cài công cụ cơ bản

1. Cài Git, Git LFS, Python 3.11, Node.js tương thích với `project/frontend/package.json`, FFmpeg có `ffprobe`, driver NVIDIA/CUDA phù hợp GPU mới. Cài Codex, Hermes Agent, 9router và ComfyUI riêng. Không sao chép venv, `node_modules`, cache hoặc file xác thực từ máy cũ.
2. Đăng nhập GitHub để đọc kho private `https://github.com/anhduyhaha1234-droid/MotionForge2D-handoff-20261019`.
3. Clone kho này. Tải **toàn bộ** asset của Release `v2026-10-19-portable` về cùng một thư mục. Nếu release/asset chưa đủ hoặc SHA không khớp, dừng phục hồi và dùng manifest xác định phần thiếu.

```powershell
git clone https://github.com/anhduyhaha1234-droid/MotionForge2D-handoff-20261019.git MotionForge2D-handoff
Set-Location .\MotionForge2D-handoff
git -C . bundle verify .\source-history.bundle
```

## 3. Kiểm và giải nén dữ liệu

Giả sử đã tải asset ZIP vào thư mục `assets` trong bản clone. Lệnh sau kiểm từng SHA-256 theo `ASSET_RELEASE_MANIFEST.json`; mọi part phải có đủ trước khi giải nén.

```powershell
$manifest = Get-Content -LiteralPath .\ASSET_RELEASE_MANIFEST.json -Raw | ConvertFrom-Json
foreach ($part in $manifest.parts) {
    $file = Join-Path .\assets $part.name
    if (-not (Test-Path -LiteralPath $file)) { throw "Thiếu $file" }
    $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $part.sha256.ToLowerInvariant()) { throw "Sai SHA-256: $file" }
}
New-Item -ItemType Directory -Path .\restored-assets -Force | Out-Null
foreach ($part in $manifest.parts) {
    Expand-Archive -LiteralPath (Join-Path .\assets $part.name) -DestinationPath .\restored-assets -Force
}
```

Archive có hai gốc logic: `project_runtime/` (projects, output, output_m05, data, SAM2 checkpoint) và `delivery_run/` (toàn bộ RUN 20261005T1643Z-wan-long trừ môi trường Python cài lại). Dùng `ASSET_RELEASE_MANIFEST.json` để đối chiếu số file/byte và archive hash. Không xoá hoặc chép đè bất kỳ workspace mới nào đã có dữ liệu trước khi sao lưu nó.

## 4. Khôi phục source và dữ liệu ở máy mới

`source-history.bundle` giữ branch/tag Git gốc. `project/` là byte source thực tế khi chụp, gồm cả thay đổi chưa commit. Trong một thư mục mới trống:

```powershell
git clone --branch master .\source-history.bundle .\MotionForge2D
robocopy .\project .\MotionForge2D /E /R:2 /W:1
git -C .\MotionForge2D status --short --branch
```

`robocopy` trả mã 0–7 cho các trường hợp sao chép thành công. Đừng dùng `/MIR`, `git reset`, `git clean` hoặc chuyển branch trong lúc phục hồi. Sao chép `restored-assets/project_runtime/` vào `MotionForge2D/` bằng `robocopy ... /E`; sao chép `restored-assets/delivery_run/` vào thư mục run riêng dưới `Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/`.

Đường dẫn cũ bắt đầu `C:\Users\Admin\...`. Nếu tên người dùng/ổ đĩa trên máy mới khác, **ghi mapping đường dẫn mới trong packet tiếp tục**, đối chiếu bằng hash rồi sửa những tham chiếu thực thi bằng patch có preimage. Không sửa báo cáo/receipt/snapshot lịch sử để làm chúng trông như được tạo trên máy mới.

## 5. Cài môi trường chạy

Trong `MotionForge2D/`, tạo venv Python 3.11 và cài theo `pyproject.toml`. Torch/CUDA dùng đúng wheel tương thích GPU mới; `pyproject.toml` pin `torch==2.11.0+cu128` và `torchvision==0.26.0+cu128`, nên có thể cần PyTorch index chính thức ngoài PyPI. Không copy wheel/venv cũ. Cài frontend bằng lockfile nếu có:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[dev]"
Set-Location .\frontend
npm ci
Set-Location ..
ffmpeg -version
ffprobe -version
```

ComfyUI trên máy cũ ở commit `73c9bad4d21e7addbe1d13bc92eee0f1431b017d` của `https://github.com/Comfy-Org/ComfyUI.git`. Cài lại repo/nodes và models theo `RUNTIME_INVENTORY.json` nếu có. **Các trọng số WAN/FLUX/VACE/Qwen/UMT5 lớn trong runtime dùng chung không được đưa vào GitHub**; lấy lại từ nguồn có quyền sử dụng và kiểm tên/kích thước/hash trước khi chạy. Không sao chép thư mục `excluded_unlicensed_weights`.

Sau đó cài lại Codex/Hermes/9router và đăng nhập tài khoản của bạn. `agent_rules/codex_skills`, `agent_rules/codex_rules`, `agent_rules/hermes_skills`, `agent_rules/HERMES_SOUL.md` là bản tham chiếu; so với bản mới trước khi cài đè. Token GitHub, API key, OAuth Antigravity, database phiên Hermes/Codex và cấu hình cục bộ có secret không nằm trong kho. Kiểm route `ag/gemini-3.8-flash-high` bằng một yêu cầu nhỏ trước khi mở owner mới; không đổi model/fallback để né quota.

## 6. Tiếp tục đúng gate

1. Trước tiên review độc lập **candidate04** theo file `review_and_handoff/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-04/`. Đối chiếu `MANIFEST.json` với source snapshot/actual bytes và `CORRECTION_MATRIX_RESULTS.json`; chỉ đọc phần đổi từ candidate03 và probe đúng các risk còn mở. Review packet 03 và snapshot review04 giúp tránh đọc/chạy lại phần hash không đổi.
2. Nếu G1 `CHANGES_REQUESTED`, cần một prompt sửa **gộp toàn bộ finding cùng cơ chế** cho một writer sau ownership/context/queue/lease audit. Session Hermes cũ không tự chuyển sang máy mới; canonical rules §4 yêu cầu bằng chứng owner cũ terminal và owner transfer/recovery receipt trước writer mới. Không dùng ID mới để xóa history/counters.
3. Nếu G1 `APPROVED` trên đúng manifest, mới cấp Gói B Media trong **một batch**: sửa hard cases, dựng và tự QC pilot 300 giây, nộp playable MP4/comparison/vision/AV evidence rồi chờ G2. G2 mới mở full source và tích hợp app; G3 mới nghiệm thu cuối.
4. Trong mọi verdict, ghi root cause, so sánh patch với thành phần hiện có/upstream, và chỉ báo phần thật sự đã xem/test. Vision helper và giới hạn native tool nằm trong `review_and_handoff/motionforge-g1-review-03-20261019/vision/`.

Prompt ngắn để đưa cho reviewer ở máy mới:

> Đọc toàn bộ `project/docs/pm/HERMES_AUTOPILOT_RULES.md`, rồi review độc lập MotionForge2D `g1-candidate-04` trong `review_and_handoff/motionforge-gemini-handoff-20261017/execution/submissions/`. Bắt đầu từ verdict candidate03, snapshot/hash/diff tại `review_and_handoff/motionforge-g1-review-04-20261019/`; chỉ đọc/probe bytes đã đổi hoặc risk còn mở. Xác minh 20 hàng matrix, byte/snapshot và test claims trước khi ra G1 verdict. Không tự mở Media nếu chưa G1 APPROVED. Nếu fail, viết một prompt correction đầy đủ cho owner hợp lệ sau audit §4; nếu pass, cấp một batch B pilot 300 giây với self-review rồi G2. Giữ một writer/GPU1, preimages, frozen evidence và Session Opening Proposal khớp verdict. Không dispatch Hermes thay tôi.

## 7. Ranh giới bản sao

Kho Git giữ source, prompts, rules và skills. GitHub Release giữ media/project DB/RUN với SHA. Những thứ **không nên chuyển máy qua GitHub**: tài khoản/token, Hermes/Codex session DB, cache cài đặt, môi trường Python/Node dựng lại, và weights runtime ngoài RUN chưa rõ quyền phân phối. `PORTABLE_SOURCE_MANIFEST.json` liệt kê chính xác file source được chụp; `ASSET_RELEASE_MANIFEST.json` liệt kê chính xác các ZIP. Nếu cần *tiếp tục đúng cùng phiên Hermes* thay vì phục hồi từ checkpoint, giữ máy cũ để xuất/migrate theo cơ chế chính thức; bản handoff này chưa chứng minh khả năng chuyển nguyên session giữa máy.
