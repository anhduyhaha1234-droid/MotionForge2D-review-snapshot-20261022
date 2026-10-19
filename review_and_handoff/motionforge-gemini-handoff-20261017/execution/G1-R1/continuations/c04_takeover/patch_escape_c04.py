import os

build_path = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\G1-R1\continuations\c04_takeover\build_g1_candidate_04.py"
with open(build_path, "r", encoding="utf-8") as f:
    src = f.read()

src = src.replace('`{fid:04d}.jpg` cho `fid in range(beg, end)`', 'dạng 4 chữ số toàn cục cho từng frame trong khoảng beg..end-1')

with open(build_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated build_g1_candidate_04.py escaping successfully")
