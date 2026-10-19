"""R6 assembly — frame-exact master + comparison source|R5|R6 (pilot [2820,11820) = 9000f).

Blend frames are 640x368 (canonical + explicit pad); encode crops 640:360:0:4 (explicit inverse).
geometry proven R4/R5: chunks tile [2820,11980); pilot = 9000 (S0074 trims tail).
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402

OUT = K.R6 / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FR = K.R6 / "assembly_frames"
AUDIO = K.TMPD / "_r6_audio_cut.m4a"


def main():
    plan = json.loads((K.D / "chunk_plan.json").read_text(encoding="utf-8"))["chunks"]
    plan = {c["unit_id"]: c for c in plan}
    used = []
    for sid in K.SHOTS:
        c = plan[sid]
        a0 = c["start_frame"]
        n = c["frames"]
        avail = min(n, K.SPAN_B - a0)
        if avail <= 0:
            continue
        bd = K.R6 / "work" / sid / "blend"
        got = len(list(bd.glob("*.jpg"))) + len(list(bd.glob("*.png")))
        if got < avail:
            raise SystemExit(f"NOT_READY: {sid} frames {got}/{avail}")
        used.append((sid, a0, n, avail))
    total = sum(u[3] for u in used)
    assert total == 9000, f"geometry total {total} != 9000"
    FR.mkdir(parents=True, exist_ok=True)
    for old in FR.glob("*.jpg"):
        old.unlink()
    for sid, a0, n, avail in used:
        bd = K.R6 / "work" / sid / "blend"
        for i in range(1, avail + 1):
            src = bd / f"{i:04d}.jpg"
            if not src.exists():
                src = bd / f"{i:04d}.png"
            dst = FR / f"{len(list(FR.glob('*.jpg'))) + 1:05d}.jpg"
            import shutil
            shutil.copyfile(src, dst)
    # silent master (explicit inverse crop)
    sil = OUT / "_r6_silent_640x360.mp4"
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", str(FR / "%05d.jpg"),
                  "-vf", "crop=640:360:0:4", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                  "-r", "30", str(sil)])
    assert r.returncode == 0, r.stderr[-300:]
    # audio cut [94,394)s
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-ss", str(K.AUDIO_SS), "-t", "300", "-i", str(K.SRC),
                  "-vn", "-c:a", "aac", "-b:a", "128k", str(AUDIO)])
    assert r.returncode == 0, r.stderr[-300:]
    master = OUT / "IDENTITY5M_R6_MASTER.mp4"
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-i", str(sil), "-i", str(AUDIO),
                  "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", str(master)])
    assert r.returncode == 0, r.stderr[-300:]
    # comparison: source | R5 master | R6 master, 9000f each, 1920x360
    r5m = K.R5 / "outputs/IDENTITY5M_R5_MASTER.mp4"
    cmp_ = OUT / "IDENTITY5M_R6_COMPARISON.mp4"
    filt = ("[0:v]trim=start=94:duration=300,setpts=PTS-STARTPTS,scale=640:360[a];"
            "[1:v]scale=640:360[b];[2:v]scale=640:360[c];[a][b][c]hstack=inputs=3[v]")
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-i", str(K.SRC), "-i", str(r5m),
                  "-ss", "300", "-i", str(master), "-filter_complex", filt, "-map", "[v]",
                  "-frames:v", "9000", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", str(cmp_)])
    assert r.returncode == 0, r.stderr[-300:]
    rec = {"frames": 9000, "shots": len(used), "master": str(master), "master_bytes": master.stat().st_size,
           "comparison": str(cmp_), "comparison_bytes": cmp_.stat().st_size,
           "crop": "640:360:0:4 explicit inverse", "audio": "[94,394)s aac",
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (K.R6 / "receipts/R6_ASSEMBLY_RECEIPT.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
