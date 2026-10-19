import os

build_path = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\G1-R1\continuations\c03_takeover\build_g1_candidate_03.py"
with open(build_path, "r", encoding="utf-8") as f:
    src = f.read()

src = src.replace('f"{i:04d}.jpg"', '0001.jpg..expect.jpg')

with open(build_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated build_g1_candidate_03.py escaping successfully")
