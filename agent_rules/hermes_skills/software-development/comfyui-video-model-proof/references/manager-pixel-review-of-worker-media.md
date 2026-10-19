# Orchestrator-side pixel review of worker media claims

A worker's JSON gate ("coverage PASS", "no watermark", "content matches") is a self-report.
Before accepting a clip, the orchestrator should **look at the pixels** — this is cheap
(ffmpeg + the vision tool) and repeatedly caught defects that every technical gate passed.
Measured cases this saved: a shot rendering the WRONG UNIT's scene; a source window spanning
a cut; a book-state event mismatched against the source; a duplicated-text transient.

## Recipe

1. Extract frames to a scratch dir (never inside the evidence root):
   `ffmpeg -hide_banner -loglevel error -i <clip> -vf "select='eq(n,0)+eq(n,60)+eq(n,119)'" -vsync 0 <out>/f_%02d.png`
   Pick first / mid / last of EACH segment (not just of the whole assembly).
2. View them against the SOURCE frame of the SAME segment window
   (`proof/inputs/<UNIT>_f000_native_WxH.png` or a frame pulled from the source clip).
   Cross-unit comparison is a trap: compare TURN's generated frame to TURN's source, not to
   BOOK's.
3. Checklist per frame — answer each explicitly, don't summarize:
   - scene identity vs the segment's own source (characters present, who holds what);
   - **object state events** (e.g. book closed → open at the manifest's event frame): a model
     can hold the right geometry all clip and still never perform the event;
   - edge-partial roles still at the frame edge (center-crop silently removes them);
   - watermark present/absent (source overlay copied into output = blocking for that profile);
   - duplicated/smeared text, doubled outlines, scene-change mid-clip.
4. Only then mark the round accepted-for-next-step. If it disagrees with the worker's JSON,
   the pixels win; record your observation as a Manager-side note with the preview path, and
   route the discrepancy as a one-variable round.

## Round discipline that made fixes converge

- One variable per round, named in the packet; keep the seed FIXED and declare what stays
  untouched.
- Fixes came in a chain, each measured: per-unit prompt → split unit at the source cut →
  per-segment prompt. Each round reran only the affected segments and appended docs; earlier
  artifacts (v1, v1.1, v1.2) stayed on disk as `supersede` markers with their own pin JSON.
  Never overwrite a previously verified artifact; the final name is
  `assembly_v1.3 = FINAL_FOR_VERIFY` with per-segment file+sha+span pins.
- Re-verify the boundary previews after every assembly rebuild (segment joins, not just the
  file header).
