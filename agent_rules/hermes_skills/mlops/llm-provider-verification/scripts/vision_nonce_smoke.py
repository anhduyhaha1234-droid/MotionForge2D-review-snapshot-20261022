#!/usr/bin/env python
"""Prove a proxied model ACTUALLY accepts images (native vision), not just claims to.

Why: a router/aggregator can return HTTP 200 while silently stripping the image
("image omitted: model has no vision support"). `/v1/models` capability flags and
`response.model` echo are NOT proof the pixels were read.

Design that makes the test un-fakeable:
  * the ground truth (a random nonce + a shuffled colour order) is rendered ONLY into
    the pixels; it is written to a JSON file that this script does NOT print;
  * stdout carries just path/sha/bytes/dims — so the caller can generate the image,
    view it natively, and only THEN read the validation file. No redirected stdout
    needed, no chance of the answer leaking into the agent's text context.

usage:
    python vision_nonce_smoke.py <out_dir>

then (in the agent):
    1. view  <out_dir>/vision_smoke_nonce.png   natively
    2. state the nonce + colour order you actually see
    3. read  <out_dir>/vision_smoke_ground_truth.json   and compare

Optional API-level check (no vision model needed on the caller side): POST the PNG as a
data URL to /v1/chat/completions and assert the response quotes the nonce, and record
`response.model` — the provider's canonical name behind the id you requested.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no look-alike 0/O/1/I
COLOURS = [("RED", (220, 30, 30)), ("GREEN", (30, 170, 60)), ("BLUE", (40, 70, 220))]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    nonce = "".join(secrets.choice(ALPHABET) for _ in range(6))
    rgb = secrets.SystemRandom().sample(COLOURS, 3)
    order = [name for name, _ in rgb]

    from PIL import Image, ImageDraw

    width, height = 720, 240
    img = Image.new("RGB", (width, height), (18, 18, 22))
    draw = ImageDraw.Draw(img)
    draw.text((24, 20), f"NONCE {nonce}", fill=(255, 255, 255))
    x = 24
    for name, colour in rgb:
        draw.rectangle([x, 80, x + 200, 200], fill=colour)
        draw.text((x + 8, 208), name, fill=(255, 255, 255))
        x += 224

    png = out_dir / "vision_smoke_nonce.png"
    img.save(png, "PNG")
    raw = png.read_bytes()

    truth = out_dir / "vision_smoke_ground_truth.json"
    truth.write_text(json.dumps({
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "png": str(png),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "dims": [width, height],
        "ground_truth_nonce": nonce,
        "ground_truth_order": order,
        "note": "withheld from the caller's text context by design; compare AFTER the native read",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # stdout deliberately carries NO ground truth
    print(json.dumps({"png": str(png), "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": len(raw), "dims": [width, height],
                      "ground_truth_file": str(truth)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
