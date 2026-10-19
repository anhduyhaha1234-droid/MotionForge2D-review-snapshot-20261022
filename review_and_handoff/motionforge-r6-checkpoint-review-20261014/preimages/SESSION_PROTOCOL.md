# Session Protocol

## 1. Context firewall

Mỗi `TASK.md` phải khai báo bốn vùng:

- `Required reading`: bắt buộc đọc đầy đủ.
- `Optional evidence`: chỉ đọc khi gặp câu hỏi cụ thể được nêu trong task.
- `Allowed write scope`: file/thư mục được phép sửa.
- `Forbidden scope`: không được sửa hoặc mở rộng.

Hermes không được tự duyệt toàn repo để tìm việc cần “cleanup”. Lệnh tìm kiếm có thể chạy trong repo khi cần định vị dependency trực tiếp, nhưng không tạo quyền sửa ngoài allowlist.

## 2. Một task phải đủ nhỏ

Task hợp lệ phải:

- tạo một outcome review được;
- có một owner/session;
- có acceptance criteria nhị phân;
- có test/evidence cụ thể;
- hoàn thành hợp lý trong một session;
- không phụ thuộc vào quyết định sản phẩm chưa được duyệt.

Nếu task vừa đổi schema, xây nhiều API, làm toàn bộ UI và migration phức tạp thì phải tách.

## 3. Quy tắc trước khi code

Hermes phải:

1. Đọc đúng required reading.
2. Kiểm tra `git status` và không ghi đè thay đổi có sẵn.
3. Ghi baseline commands/results vào `LOG.md`.
4. Tóm tắt plan ngắn trong chat.
5. Dừng và báo `BLOCKED` nếu requirement mâu thuẫn, migration có nguy cơ mất dữ liệu hoặc cần mở rộng write scope.

### Byte checkpoint trước writer

Trước khi sửa file hiện hữu, đặc biệt file untracked/dirty, test authority hoặc
file lớn không thể restore từ Git, owner/Manager phải:

- ghi SHA-256, byte size, line count và tracked/dirty attribution;
- tạo byte snapshot trong task evidence và xác minh snapshot hash;
- lưu manifest bằng `docs/pm/tools/write_set_guard.py` hoặc guard tương đương;
- pin protected-file hashes và ngưỡng destructive shrink trước dispatch.

Manager chỉ tạo/verify evidence; Manager không được dùng snapshot để tự sửa
implementation.

## 4. Quy tắc trong khi code

- Không sửa PRD, MP, roadmap hoặc task contract.
- Không đổi public contract ngoài phần task cho phép.
- Không xóa dữ liệu người dùng.
- Không “tiện thể” sửa lỗi lint/refactor ngoài scope.
- Mọi schema change phải có migration và backward/upgrade test.
- Business state bền vững không được chỉ nằm trong RAM, Zustand hoặc localStorage.
- Long-running operation không chạy đồng bộ trong request/UI.
- Frontend phải tuân thủ `frontend/AGENTS.md` và đọc tài liệu Next.js local liên quan trước khi code.
- Không che test fail bằng skip, ignore hoặc nới assertion nếu task không cho phép.
- File đã tồn tại chỉ được sửa bằng bounded patch có preimage. Cấm `write_file`,
  full-file replace, shell redirection, `Set-Content`, `Out-File`, heredoc,
  script direct-write hoặc copy/move-overwrite vào source/test hiện hữu. Chỉ file
  mới chưa tồn tại trong allowlist mới được whole-file generation.
- Sau mỗi patch phải kiểm lại hash/byte/line count. Nếu file mất, giảm bất
  thường hoặc guard báo destructive shrink thì dừng writer ngay; không tiếp tục
  implementation hoặc broad gate.

## 5. Deliverables bắt buộc

Trước khi submit, Hermes phải:

- chạy validation ghi trong task;
- chạy targeted tests cho thay đổi;
- cập nhật `REPORT.md` theo template;
- append các hành động/kết quả quan trọng vào `LOG.md`;
- ghi rõ test nào không chạy và lý do;
- liệt kê file thay đổi;
- để trạng thái `SUBMITTED`, không tự nhận `APPROVED`.

## 6. PM review

### Single-writer handshake (mandatory)

- Chỉ một writer được phép hoạt động trên worktree tại mọi thời điểm.
- Khi Hermes đang chạy, PM/Antigravity chỉ được đọc; không được sửa file, tạo packet kế tiếp, chạy quality gate làm thay đổi artifact, hoặc commit.
- Hermes phải kết thúc tiến trình sau khi ghi `REPORT.md = SUBMITTED`.
- PM chỉ được bắt đầu review sau khi Hermes đã thoát và working tree đã ổn định.
- PM review phải ghi đúng commit/tree được review, Quality Run ID, và thời điểm review. Review không được có timestamp sớm hơn lần cập nhật cuối của REPORT/LOG.
- PM không được sửa implementation trong lúc review. Nếu cần sửa, ghi `CHANGES_REQUESTED` và resume đúng Hermes session.
- Ở chế độ review từng task, chỉ `APPROVED` hợp lệ mới cho phép commit/close
  task và tạo packet task kế tiếp.
- Ở chế độ full-sprint đã được PM ghi rõ trong sprint contract, Hermes manager
  được mở dependency nội bộ kế tiếp sau khi writer thoát và manager ghi
  `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`. Trạng thái này không phải PM
  approval. Mặc định nó không cho phép commit/merge/push; ngoại lệ chỉ khi prompt
  hiện hành cấp rõ isolated-worktree transport: product worker commit đúng
  allowlist trên task branch, một integration owner riêng merge exact commit đã
  Manager verify và push canonical sau green wave gate. Ngoại lệ Git này không
  nâng trạng thái thành `APPROVED`.

PM kiểm tra theo thứ tự:

1. Scope compliance.
2. Acceptance criteria.
3. Architecture/domain compatibility.
4. Data safety/migration.
5. Tests và evidence.
6. UX states nếu có UI.
7. Regression risk.

Nếu chưa đạt, PM không sửa lẫn vào task hiện tại. PM ghi `CHANGES_REQUESTED` với danh sách hữu hạn; Hermes tiếp tục đúng session hoặc PM tạo repair task riêng.

### Incident source/test destruction

- Bảo toàn ngay file hỏng, snapshot, cache/pyc, tool logs và state database;
  không chạy command có thể ghi đè evidence trước khi freeze hash.
- Manager/PM không reconstruct source/test. Exact worker owner hoặc recovery
  owner được Codex cấp quyền phải dựng candidate bên ngoài path chính từ byte
  snapshot/full tool payload/deterministic patch replay.
- Nếu có reviewed SHA, candidate phải match exact SHA trước khi patch file
  chính. Compile, node-name match hoặc semantic rewrite không thay thế exact
  source authority.
- Full relevant module phải được collect/run và report cả fail lẫn pass; selection
  xanh không được đại diện cho toàn file.
- Một guarded resume được phép khi Codex cấp quyền. Vi phạm overwrite/scope lần
  hai phải dừng `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.

## 7. Session handoff

Mặc định, task kế tiếp chỉ được dùng các output đã được PM approve. Dependency
chưa approve được coi là chưa tồn tại. Mỗi `TASK.md` mới phải trỏ chính xác đến
report/contract được phép kế thừa.

Ngoại lệ full-sprint chỉ áp dụng khi PM đã phát hành trước toàn bộ sprint
contract và task packets. Trong phạm vi đó, task phụ thuộc nội bộ được dùng
output `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` của task trước. Hermes manager
không được tự tạo/thay đổi acceptance contract, mở task ngoài sprint, hoặc dùng
manager gate để thỏa dependency của sprint/epic khác.

Luồng trạng thái bắt buộc:

`READY -> HERMES_RUNNING -> SUBMITTED_PENDING_PM -> CHANGES_REQUESTED -> HERMES_RUNNING`

hoặc:

`READY -> HERMES_RUNNING -> SUBMITTED_PENDING_PM -> APPROVED -> CLOSED`

Hoặc, trong chế độ full-sprint do PM phát hành:

`READY -> HERMES_RUNNING -> SUBMITTED_PENDING_MANAGER -> CHANGES_REQUESTED -> HERMES_RUNNING`

hoặc:

`READY -> HERMES_RUNNING -> SUBMITTED_PENDING_MANAGER -> MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`

Sau task cuối:

`MANAGER_VERIFIED_PENDING_SPRINT_REVIEW -> SPRINT_SUBMITTED -> PM_SPRINT_REVIEW -> APPROVED -> CLOSED`

Nếu Codex trả correction ở sprint exit:

`SPRINT_SUBMITTED -> CHANGES_REQUESTED ->` resume đúng session của Task ID liên
quan `-> SPRINT_SUBMITTED`.

Không được nhảy trực tiếp từ `HERMES_RUNNING` sang `APPROVED`. Không được có hai
Task ID ghi đồng thời trên cùng worktree; nhiều writer chỉ hợp lệ trên các clean
worktree/branch tách biệt, đúng parallel wave và resource isolation đã được PM
cấp trước.

### Full-sprint manager gate

- PM phải chuẩn bị sprint contract, dependency graph, mọi task packet, allowed
  write scope và protected-data baseline trước khi manager chạy task đầu tiên.
- Mỗi Task ID vẫn dùng một Hermes coding session riêng. Correction của cùng Task
  ID phải resume đúng stored session ID.
- Manager chỉ review sau khi writer thoát và tree ổn định; phải audit scope/diff,
  chạy validation và ghi exact session/evidence.
- `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` chỉ mở dependency nội bộ tuyến tính;
  không phải `APPROVED` và Hermes không được sửa `PM_REVIEW.md`.
- Manager chạy fresh sprint-exit integration, Playwright/visual (nếu liên quan),
  quality baseline và protected-data comparison, rồi dừng mọi writer ở
  `SPRINT_SUBMITTED`.
- Codex chỉ review khi người dùng yêu cầu ở sprint exit. Không tự poll tiến trình
  Hermes trong lúc sprint đang chạy.
- Parallel writers chỉ được phép khi sprint contract cho phép rõ ràng, worktree,
  session, write scope và mutable runtime/evidence hoàn toàn tách biệt. Task có
  dependency trực tiếp phải chạy tuần tự.
