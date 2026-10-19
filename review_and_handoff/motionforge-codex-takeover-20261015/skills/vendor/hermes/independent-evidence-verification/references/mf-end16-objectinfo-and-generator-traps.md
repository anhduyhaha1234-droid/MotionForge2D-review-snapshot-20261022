# Object-info false negatives, file-widget exemptions, generator dry-run (measured 2026-09-28, MF-END-16)

Three traps found while offline-validating a ComfyUI graph against captured `/object_info`
dumps and while re-running a JSON generator after commit. All three produced a "plausible
failure" that was actually a measurement bug — same family as blanket-100 % mismatches.

## 1. A `/object_info` dump captured WITHOUT the model root has EMPTY file-widget option lists

`P0_object_info.json` (server started without `--models-directory`) reported
`VAELoader.vae_name` options as `['pixel_space']` and `UNETLoader.unet_name` as `[[]]`.
Validating a graph whose `vae_name` is a real file then fails with
`'Wan2_1_VAE_bf16.safetensors' not in ['pixel_space']` — a FALSE negative.
The dump captured on the GPU server that ran the jobs (`P3_object_info_gpu.json`,
`--models-directory` at the shared root) lists the real files and validates 0 errors.
Rule: pin the dump taken in the SAME server configuration that ran the jobs; if two dumps
exist, diff their option lists before choosing one.

## 2. File-selector widgets are input-dir SNAPSHOTS, not semantic enums

`LoadImage.image`, `LoadVideo.file`, `LoadAudio.audio` option lists enumerate the input
directory at capture time. A delivered graph's staged filename (created later) is never in
that list. Exempt these widgets from enum membership checks; bind the exact filename + sha256
in a separate case table instead. Keep counting them as "checked" so the proof still reports
coverage. Everything else (sampler_name, weight_dtype, clip type...) stays enum-checked.

## 3. A generator that embeds a timestamp overwrites committed bytes on re-run — add `--verify`

A build script embedding `generated_at_utc` was re-run without arguments after its commit, so
the three delivered JSONs changed (only the timestamp + the manifest's derived
`graph_file_sha256` line), dirtying a supposedly-final tree. Recovery: `git checkout HEAD -- <own
paths>` restored the committed bytes (owner unambiguous, history not rewritten) — verify with
porcelain 0 + sha256. Prevention: add a `--verify` mode that rebuilds IN MEMORY with the
on-disk timestamps and byte-compares without writing; it doubles as the determinism proof
(expected delta = only the timestamp field). Never run the write mode after the final gate.

## 4. Model provenance: HF LFS oid == locally measured sha256

For each model file, `GET /api/models/<repo>/tree/main?recursive=true&revision=<rev>` returns
`size` + `lfs.oid`; hashing the local file and comparing all three (name, size, oid==sha256)
proves provenance + revision + license (from `/api/models/<repo>/revision/<rev>` cardData)
without trusting a filename. Save the probe JSON as raw evidence.
