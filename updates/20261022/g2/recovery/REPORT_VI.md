# G2-B2-RECOVER-01 — recovery vault chờ root review

**Verdict: `SELF_VERIFIED_PENDING_ROOT_REVIEW`.** Chỉ ba input có provenance được chép nguyên byte vào `vault-g2b2-001`. Receipt có 25 PASS, 1 UNVERIFIED (graph runtime), 0 FAIL. G2 media vẫn BLOCKED; pilot 300 giây, model inference, render và service đều NOT_RUN.

| Input trong vault | Byte | SHA-256 |
| --- | ---: | --- |
| `task/corrections/identity/r6/source_actor_ledger.jsonl` | 36,876 | `1012a20a03b10e91a22e1e7a588e4f6b7f8259599f90f0d4fd855bec9f9c3715` |
| `task/corrections/identity/r6/cast_atlas.json` | 4,120 | `e847acb8d30f120bcaffb81b1e5048baf3e32280bcd74e9e5688b20a56149a4e` |
| `task/graph/reuse_bundle/shot_anchor_v1.baseline.api.json` | 16,804 | `0ff8ed9c92441230d76d42f2d3eeffb92e70f1b8749f663b170d1566a3df7f4e` |

## Provenance và giới hạn

Ledger và atlas đến từ snapshot R6 tại `C:/Users/Admin/Documents/Codex/work/mf-portable-handoff-20261019/review_and_handoff/motionforge-r6-checkpoint-review-20261014/`; `PACKET_MANIFEST.json` SHA `0f8785bda71c1fd8ea2374da7adc10eee5775eaeb79ad00ceaae586e691ae5e8` khai đúng size/hash cho cả hai. Ledger có 54 dòng S0021–S0074, full-shot liên tục `[2820,11980)` ở 30 fps. Atlas có 14 pin CAST PNG duy nhất; ledger tham chiếu đúng tên front trong atlas. Đây là kiểm tra cấu trúc, không xác nhận sự thật ngữ nghĩa của từng actor hay sự tồn tại của PNG.

Graph lấy từ `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-rebuild-skills-20261001/reuse_bundle/`. `PROVENANCE.json` SHA `7b536305b093b10827a5e4732de6ff23057e830e433d2e5b6c209000b82f1971` nối graph 48 node với wrapper gốc và snapshot cùng SHA `e02574f799cfac6477be455aa18ff68e02f5ba5ed34c2651dba55d8496f266c6`. Hai bản graph lịch sử khác tại external-review 20261002 và WAN prototype có cùng 16,804 byte/hash. Các file `r6_graph.py`, `r6_key_recipe.py`, `r6_ledger.py` trong pilot được manifest G1 C16 pin; code R6 đọc đúng template path và nối `GUIDER` tới `R2_POS/R2_NEG`. Kiểm tra tĩnh xác nhận 48 node, tất cả link tham chiếu node tồn tại, FLUX.2 Klein 4B/4 steps/Euler/CFG1, KEY + R1/R2 CAST nằm trong conditioning và R3 ngoài chain sau rewire. **Khả năng node API/runtime/model thực thi vẫn UNVERIFIED** vì scope không cho khởi động service, load model hay chạy graph.

Không chép storyboard fixture S0021, không tạo hoặc repin 14 CAST PNG. Vault cũng không được đưa vào pilot đã duyệt; chỉ root có thể quyết định transport kế tiếp. Các gap B1 khác như storyboard đầy đủ, input media, model phụ thuộc, Python runtime, endpoint và lease vẫn còn.

## Lệnh, exit và self-review

Working directory: `C:/Users/Admin/Documents/Codex/g2b2-recovery/`; `PYTHONDONTWRITEBYTECODE=1` và `python -B`.

```powershell
python -B -m unittest -v test_recover
# exit 0; 6/6 PASS, chạy âm tính trước positive; raw log TESTS.txt

python -B recover.py --vault C:/Users/Admin/Documents/Codex/g2b2-recovery/vault-g2b2-001 --receipt C:/Users/Admin/Documents/Codex/g2b2-recovery/RECEIPT.json
# exit 0; SELF_VERIFIED_PENDING_ROOT_REVIEW; 3 copied

$v='C:\Users\Admin\Documents\Codex\g2b2-recovery\vault-g2b2-001'
Get-ChildItem -LiteralPath $v -Recurse -File | ForEach-Object {
  $rel=$_.FullName.Substring($v.Length+1)
  $sha=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
  Write-Output "$rel`n  bytes=$($_.Length) sha256=$sha"
} | Tee-Object -FilePath 'C:\Users\Admin\Documents\Codex\g2b2-recovery\POSTIMAGE.txt'
# exit 0; ba hash và byte trong POSTIMAGE.txt khớp nguồn/pin
```

Tests âm tính xác nhận source thêm byte, đường dẫn `../`, đích trùng khác hoa-thường, graph link sai và overwrite đều bị chặn; không tạo vault trong các case preflight fail. Code từ chối symlink/reparse, nguồn không phải regular file, JSON duplicate keys, pin sai, trùng đích/case, path escape và vault có sẵn. Nó preflight nguồn/authority/schema trước copy, tạo đích bằng `xb`, hash hậu ảnh và kiểm inventory chỉ ba file. Source có thể đổi giữa preflight và copy thì postimage FAIL, không tự tuyên bố verified. Root review B1, checkpoint, pilot manifest và B1 receipt vẫn giữ hash cũ sau task. Không có `.pyc` được tạo trong candidate/pilot.

Artefact: `RECEIPT.json` SHA-256 `d0ff8b2a33b3fd6bacb4839d0c633a0293f8a5a0d70f7f8b3093a4d8e79da70e`; `recover.py` SHA-256 `3479e6e8707ac58568460330c622873660fa05ca5f26604ffb919590b3fe8f00`; `test_recover.py` SHA-256 `30bb7dfc6274930dfe6b31db6debe9feb6fba23c1959586b0355b1b48a4de6b3`. Dừng ở đây để root review exact vault/postimage; không mở G2 media.
