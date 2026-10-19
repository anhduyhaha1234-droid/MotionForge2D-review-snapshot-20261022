# S12-C2 W4→W5 cross-lane result-endpoint gap (2026-09-09)

## Tình huống

C2 prompt §4 T03C bắt buộc "Scoped result playback/download endpoints +
server-owned project/video export context (C22-part backend)". Worker T03C
commit `8753f2a` (30 passed, ruff/diff clean, merged canonical `1d6e5ad`)
đóng F01/F02/F07 + rows C01–C18 — NHƯNG không có result endpoints, và
REPORT_C2 row list không nhắc C22. T05 (frontend lane, base `1d6e5ad`)
phát hiện gap bằng probe live:

```
routes canonical (grep -n "@router" app/api/routes/s12_export.py):
  POST /s12-exports/submit
  GET  /s12-exports/{run_id}
  POST /s12-exports/{run_id}/cancel
  POST /s12-exports/{run_id}/retry
→ GET /s12-exports/{run}/result|download|media|output: tất cả 404
```

## Quyết định (không phá ownership, không fake)

1. **Verifier bằng grep thật**: Manager grep routes trong canonical, đối chiếu
   danh sách endpoint prompt hứa — REPORT worker không được dùng làm chứng.
2. **Route về đúng owner**: resume T03C SAME session (`20260907_144542_7d5dbf`)
   với BOUNDED ADDENDUM — delta liệt kê chính xác:
   - `GET /s12-exports/{run_id}/result` — metadata + server-owned media URL,
     chỉ khi run completed + ownership đúng + authority;
   - `GET /s12-exports/{run_id}/media` — stream/download file thật (playable),
     authorization completed + owned; stale/partial/missing/tampered → 404/403
     fail-closed;
   - tests cho cả 2 endpoint (valid play/download + denied cases);
   - REPORT_C2 cập nhật C22-part.
   Prompt: `t03c-addendum-*` trong C2 root. Không để T05 giả lập endpoint hay
   SQL-seed quanh gap.
3. **Consumer tiếp tục song song**: T05 tiếp tục phần độc lập (C20 bỏ manual
   pins UI rewrite, harness safety F10) — write-set disjoint frontend vs
   backend nên chạy đồng thời không xung đột.
4. **Verify sau merge**: chỉ sau khi addendum land + INT01 merge, T05 mới
   chứng minh C22 positive qua REAL endpoint.

## Dấu hiệu nhận biết chung

- Worker REPORT đóng rows nhưng bỏ 1 row prompt gán cho nó (C22-part) →
  incomplete promise: so REPORT row list vs prompt §5 rows TRƯỚC khi merge.
- Consumer lane (frontend/verifier) probe API live đầu wave — 404 trên
  endpoint đã hứa = gap thật, không phải "sẽ có sau".
- Addendum = resume exact session trên merged tip (không branch mới, không
  INT01 mới, không Manager tự code).