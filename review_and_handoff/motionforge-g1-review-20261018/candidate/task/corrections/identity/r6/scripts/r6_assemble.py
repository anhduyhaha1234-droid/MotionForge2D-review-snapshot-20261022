"""R6g assembly — frame-exact master + comparison (source94s | R5frame0 | R6G frame0), NEW namespace.

F02: gate_assemble(shot_plan) is called BEFORE any copying/encoding — the encoder cannot run when
     reviews/manifests are missing/stale/unknown.
F09: inputs start at frame 0 (no `-ss 300` before the master input); all three sources 9000 frames.
Frames sourced from each shot's manifest blend_dir (validated by the gate).
"""
from __future__ import annotations
import json, os, shutil, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402

NS = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))
OUT = NS / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FR = NS / "assembly_frames"
AUDIO = NS / "_r6g_audio_cut.m4a"


def shot_blend_dir(sid):
    man = K.R6 / "work" / sid / "blend_manifest.json"
    if man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        if m.get("blend_dir"):
            return Path(m["blend_dir"])
    return K.R6 / "work" / sid / "blend"


def main():
    plan = json.loads((K.D / "chunk_plan.json").read_text(encoding="utf-8"))["chunks"]
    plan = {c["unit_id"]: c for c in plan}
    used = []
    for sid in K.SHOTS:
        c = plan[sid]
        a0, n = c["start_frame"], c["frames"]
        avail = min(n, K.SPAN_B - a0)
        if avail <= 0:
            continue
        used.append((sid, a0, n, avail))
    total = sum(u[3] for u in used)
    assert total == 9000, f"geometry total {total} != 9000"
    # F02: gate ALL consumers BEFORE the encoder.
    G.gate_assemble([(sid, avail) for sid, a0, n, avail in used])
    FR.mkdir(parents=True, exist_ok=True)
    for old in FR.glob("*.jpg"):
        old.unlink()
    counter = 0
    for sid, a0, n, avail in used:
        m = json.loads((K.R6 / "work" / sid / "blend_manifest.json").read_text(encoding="utf-8"))
        bd = Path(m["blend_dir"])
        for fr in m["frames"][:avail]:
            counter += 1
            shutil.copyfile(bd / fr["name"], FR / f"{counter:05d}.jpg")
    assert counter == 9000, f"copied {counter}"
    sil = NS / "_r6g_silent_640x360.mp4"
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", str(FR / "%05d.jpg"),
                  "-vf", "crop=640:360:0:4", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                  "-r", "30", str(sil)])
    assert r.returncode == 0, r.stderr[-300:]
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-ss", str(K.AUDIO_SS), "-t", "300", "-i", str(K.SRC),
                  "-vn", "-c:a", "aac", "-b:a", "128k", str(AUDIO)])
    assert r.returncode == 0, r.stderr[-300:]
    master = OUT / "R6G_MASTER.mp4"
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-i", str(sil), "-i", str(AUDIO),
                  "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", str(master)])
    assert r.returncode == 0, r.stderr[-300:]
    # comparison: all inputs from frame0 (F09)
    r5m = K.R5 / "outputs/IDENTITY5M_R5_MASTER.mp4"
    cmp_ = OUT / "R6G_COMPARISON.mp4"
    filt = ("[0:v]trim=start=94:duration=300,setpts=PTS-STARTPTS,scale=640:360[a];"
            "[1:v]scale=640:360[b];[2:v]scale=640:360[c];[a][b][c]hstack=inputs=3[v]")
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-i", str(K.SRC), "-i", str(r5m), "-i", str(master),
                  "-filter_complex", filt, "-map", "[v]", "-frames:v", "9000", "-c:v", "libx264",
                  "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", str(cmp_)])
    assert r.returncode == 0, r.stderr[-300:]
    rec = {"frames": 9000, "shots": len(used), "master": str(master), "master_bytes": master.stat().st_size,
           "comparison": str(cmp_), "comparison_bytes": cmp_.stat().st_size,
           "crop": "640:360:0:4 explicit inverse", "audio": "[94,394)s aac", "inputs_frame0": True,
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (NS / "receipts").mkdir(parents=True, exist_ok=True)
    (NS / "receipts/R6G_ASSEMBLY_RECEIPT.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
