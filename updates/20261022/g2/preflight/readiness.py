"""G2-B1-PREFLIGHT-01: CPU-only, read-only media readiness inventory.

Only the explicit JSON output path is written. Project modules are inspected as
bytes/AST, never imported: r6_common imports would create directories in pilot.
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import stat
import subprocess
import sys
import urllib.error
import urllib.request

from PIL import Image


WRITE_ROOT = Path(r"C:\Users\Admin\Documents\Codex\g2b1-readiness")
PILOT = Path(r"C:\Users\Admin\Documents\Codex\g2p01-transport\pilot-g2p01-001")
C16 = Path(
    r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2"
    r"\outputs\motionforge-g1-review-04-20261020\submissions\g1-candidate-16"
)
TRANSPORT_RECEIPT = Path(r"C:\Users\Admin\Documents\Codex\g2p01-transport\receipts\positive-001.json")
ROOT_REVIEW = Path(r"C:\Users\Admin\Documents\Codex\g2-readiness-audit\ROOT_REVIEW_G2P01.md")
ATLAS = Path(
    r"C:\Users\Admin\Documents\Codex\work\mf-portable-handoff-20261019"
    r"\review_and_handoff\motionforge-r6-checkpoint-review-20261014\snapshot"
    r"\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\cast_atlas.json"
)
HISTORICAL_LEDGER = ATLAS.parent / "source_actor_ledger.jsonl"
RUNTIME = Path(r"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b")
MANIFEST_SHA = "4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82"
RECEIPT_SHA = "e9bf67facc7e6a0debc0d8251460551a26d7cface9a264ae8d78f3ec388bb47f"
ROOT_REVIEW_SHA = "6bfb1d71b900a84ca84df0e765c839202a24c96cf90738577c1c1c36aaa082ce"
ATLAS_SHA = "e847acb8d30f120bcaffb81b1e5048baf3e32280bcd74e9e5688b20a56149a4e"
SOURCE_SHA = "5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2"
SOURCE_BYTES = 36_971_916
SOURCE_REL = "task/source/source_full.mp4"
PLAN_REL = "task/chunk_plan.json"
SPAN_A, SPAN_B, FPS = 2820, 11820, 30
EXPECTED_SHOTS = [f"S{i:04d}" for i in range(21, 75)]
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def reparse_ancestor(path: Path) -> str | None:
    for parent in path.parents:
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if getattr(info, "st_file_attributes", 0) & REPARSE or parent.is_symlink():
            return str(parent)
    return None


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def check(check_id: str, status: str, reason: str, **evidence: object) -> dict:
    assert status in {"PASS", "FAIL", "UNKNOWN"}
    return {"id": check_id, "status": status, "reason": reason, "evidence": evidence}


def file_facts(path: Path, *, full_hash: bool = True) -> dict:
    result = {"path": str(path), "exists": False, "bytes": None, "sha256": None}
    escaped = reparse_ancestor(path)
    if escaped:
        result["error"] = f"reparse ancestor: {escaped}"
        return result
    try:
        info = path.lstat()
    except FileNotFoundError:
        return result
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
        result["error"] = "not a regular, non-reparse file"
        return result
    result["exists"] = True
    result["bytes"] = info.st_size
    if full_hash:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result["sha256"] = digest.hexdigest()
    return result


def read_json(path: Path) -> dict:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key {key}")
            value[key] = item
        return value

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def safe_relative(raw: object) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise ValueError(f"unsafe relative path: {raw!r}")
    name = PurePosixPath(raw)
    if name.is_absolute() or name.as_posix() != raw or any(p in ("..", ".", "") or ":" in p for p in name.parts):
        raise ValueError(f"unsafe relative path: {raw!r}")
    return raw


def inventory(root: Path) -> dict[str, Path]:
    escaped = reparse_ancestor(root)
    if escaped:
        raise ValueError(f"reparse ancestor: {escaped}")
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
        raise ValueError(f"unsafe tree root: {root}")
    found = {}
    stack = [root]
    while stack:
        directory = stack.pop()
        for item in os.scandir(directory):
            path = Path(item.path)
            info = item.stat(follow_symlinks=False)
            if item.is_symlink() or getattr(info, "st_file_attributes", 0) & REPARSE:
                raise ValueError(f"reparse point: {path}")
            if stat.S_ISDIR(info.st_mode):
                stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                found[safe_relative(path.relative_to(root).as_posix())] = path
            else:
                raise ValueError(f"nonregular tree entry: {path}")
    return found


def check_authority() -> list[dict]:
    checks = []
    for label, path, pin in (
        ("transport_receipt", TRANSPORT_RECEIPT, RECEIPT_SHA),
        ("root_review", ROOT_REVIEW, ROOT_REVIEW_SHA),
    ):
        facts = file_facts(path)
        good = facts["sha256"] == pin
        checks.append(check(label, "PASS" if good else "FAIL", "pinned authority bytes" if good else "missing or changed authority", file=facts, expected_sha256=pin))
    if checks[0]["status"] == "PASS":
        try:
            receipt = read_json(TRANSPORT_RECEIPT)
            good = (
                receipt.get("transport_status") == "SELF_VERIFIED_PENDING_ROOT_REVIEW"
                and receipt.get("process_exit_code") == 0
                and receipt.get("pins", {}).get("manifest_sha256") == MANIFEST_SHA
                and receipt.get("pins", {}).get("source_sha256") == SOURCE_SHA
            )
            checks.append(check("transport_receipt_contract", "PASS" if good else "FAIL", "transport receipt verdict and pins", receipt_status=receipt.get("transport_status"), receipt_exit=receipt.get("process_exit_code")))
        except (OSError, ValueError, KeyError) as exc:
            checks.append(check("transport_receipt_contract", "FAIL", str(exc)))
    else:
        checks.append(check("transport_receipt_contract", "UNKNOWN", "receipt bytes not authoritative"))
    return checks


def check_manifest_tree(root: Path, manifest_sha: str, source_pin: tuple[int, str] | None, *, expected_declared: int | None = None, check_id: str = "pilot_bytes") -> dict:
    evidence = {"root": str(root), "manifest": file_facts(root / "MANIFEST.json")}
    if evidence["manifest"]["sha256"] != manifest_sha:
        return check(check_id, "FAIL", "manifest missing or SHA mismatch", **evidence, expected_manifest_sha256=manifest_sha)
    try:
        manifest = read_json(root / "MANIFEST.json")
        rows = manifest["files"]
        if not isinstance(rows, list) or manifest.get("total_files") != len(rows):
            raise ValueError("manifest count mismatch")
        if expected_declared is not None and len(rows) != expected_declared:
            raise ValueError(f"expected {expected_declared} declared files, got {len(rows)}")
        expected = {}
        folded = set()
        for row in rows:
            rel = safe_relative(row["relative"])
            if rel.casefold() in folded or rel in ("MANIFEST.json", SOURCE_REL):
                raise ValueError(f"duplicate or reserved relative path: {rel}")
            if type(row["bytes"]) is not int or row["bytes"] < 0 or not SHA_RE.fullmatch(row["sha256"]):
                raise ValueError(f"invalid manifest row: {rel}")
            expected[rel] = row
            folded.add(rel.casefold())
        actual = inventory(root)
        expected_paths = set(expected) | {"MANIFEST.json"}
        if source_pin is not None:
            expected_paths.add(SOURCE_REL)
        evidence["file_count"] = len(actual)
        evidence["missing"] = sorted(expected_paths - set(actual))
        evidence["extra"] = sorted(set(actual) - expected_paths)
        mismatch = []
        for rel, row in sorted(expected.items()):
            if rel in actual:
                facts = file_facts(actual[rel])
                if facts["bytes"] != row["bytes"] or facts["sha256"] != row["sha256"]:
                    mismatch.append({"relative": rel, "actual": facts, "expected_bytes": row["bytes"], "expected_sha256": row["sha256"]})
        evidence["mismatches"] = mismatch
        if source_pin is not None:
            evidence["source"] = file_facts(root / SOURCE_REL)
            evidence["source_expected"] = {"bytes": source_pin[0], "sha256": source_pin[1]}
            source_ok = evidence["source"]["bytes"] == source_pin[0] and evidence["source"]["sha256"] == source_pin[1]
        else:
            source_ok = True
        good = not evidence["missing"] and not evidence["extra"] and not mismatch and source_ok
        return check(check_id, "PASS" if good else "FAIL", "exact manifest inventory and source bytes" if good else "inventory or bytes differ", **evidence)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return check(check_id, "FAIL", str(exc), **evidence)


def check_source_probe(source: Path) -> dict:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate", "-of", "json", str(source)]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        evidence = {"path": str(source), "command": command, "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
        if run.returncode:
            return check("source_probe", "FAIL", "ffprobe returned nonzero", **evidence)
        probe = json.loads(run.stdout)
        streams = probe["streams"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        audio = [s for s in streams if s.get("codec_type") == "audio"]
        good = (
            len(streams) == 2 and len(video) == 1 and len(audio) == 1
            and video[0].get("codec_name") == "h264" and video[0].get("width") == 640 and video[0].get("height") == 360
            and Fraction(video[0]["r_frame_rate"]) == 30 and Fraction(video[0]["avg_frame_rate"]) == 30
            and audio[0].get("codec_name") == "aac" and Decimal(probe["format"]["duration"]) == Decimal("1321.215420")
        )
        return check("source_probe", "PASS" if good else "FAIL", "source H.264/AAC shape, FPS and duration", **evidence)
    except (OSError, subprocess.TimeoutExpired, KeyError, ValueError, TypeError) as exc:
        return check("source_probe", "UNKNOWN", str(exc), path=str(source), command=command, exit_code=None)


def check_plan(path: Path, span: tuple[int, int] = (SPAN_A, SPAN_B), expected_shots: list[str] = EXPECTED_SHOTS) -> dict:
    facts = file_facts(path)
    evidence = {"file": facts, "span": list(span), "fps": FPS, "expected_shots": expected_shots}
    if not facts["exists"]:
        return check("plan_300s", "FAIL", "chunk plan missing", **evidence)
    try:
        plan = read_json(path)
        chunks = plan["chunks"]
        selected = [c for c in chunks if c.get("unit_id") in expected_shots]
        ids = [c["unit_id"] for c in selected]
        if len(ids) != len(expected_shots) or set(ids) != set(expected_shots) or len(set(ids)) != len(ids):
            raise ValueError("S0021-S0074 selection is missing or duplicated")
        selected.sort(key=lambda c: c["start_frame"])
        if selected[0]["unit_id"] != "S0021" or selected[0]["start_frame"] != SPAN_A:
            raise ValueError("S0021 does not start at global frame 2820")
        if selected[-1]["unit_id"] != "S0074" or (selected[-1]["start_frame"], selected[-1]["end_frame"]) != (11679, 11980):
            raise ValueError("S0074 full-shot span differs from [11679,11980)")
        used = []
        cursor = span[0]
        for c in selected:
            start, end = c["start_frame"], c["end_frame"]
            if type(start) is not int or type(end) is not int or end <= start or c.get("frames") != end - start:
                raise ValueError(f"invalid full-shot frame span: {c.get('unit_id')}")
            if c.get("trim") != {"start_frame": start, "end_frame": end}:
                raise ValueError(f"declared source trim differs from full-shot span: {c['unit_id']}")
            use_start, use_end = max(start, span[0]), min(end, span[1])
            if use_start != cursor or use_end <= use_start:
                raise ValueError(f"pilot coverage gap/overlap at {c['unit_id']}: cursor {cursor}, start {use_start}")
            used.append({"shot": c["unit_id"], "full": [start, end], "pilot": [use_start, use_end], "pilot_frames": use_end - use_start})
            cursor = use_end
        if cursor != span[1] or sum(row["pilot_frames"] for row in used) != 9000:
            raise ValueError(f"pilot coverage {cursor} does not end at {span[1]}")
        evidence["touched_shots"] = len(used)
        evidence["used_frames"] = 9000
        evidence["last_shot"] = used[-1]
        evidence["last_shot_excluded_tail_frames"] = used[-1]["full"][1] - span[1]
        evidence["pilot_cut_seconds"] = [span[0] / FPS, span[1] / FPS]
        return check("plan_300s", "PASS", "54 contiguous shots cover [2820,11820); final S0074 is explicitly clipped", **evidence)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return check("plan_300s", "FAIL", str(exc), **evidence)


def check_cast(atlas_path: Path, atlas_sha: str, cast_dir: Path, *, minimum_bytes: int = 1024) -> list[dict]:
    atlas_facts = file_facts(atlas_path)
    evidence = {"file": atlas_facts, "expected_sha256": atlas_sha, "cast_dir": str(cast_dir)}
    if atlas_facts["sha256"] != atlas_sha:
        return [check("cast_atlas", "FAIL", "historical atlas missing or hash changed", **evidence)]
    try:
        atlas = read_json(atlas_path)
        assets = {}
        for entity, record in atlas["entities"].items():
            for view in ("front", "profile"):
                row = record[view]
                name, digest = row["file"], row["sha256"]
                if not isinstance(name, str) or name != Path(name).name or ":" in name or not name.endswith(".png") or not SHA_RE.fullmatch(digest):
                    raise ValueError(f"invalid CAST pin: {entity}/{view}")
                if name in assets and assets[name]["expected_sha256"] != digest:
                    raise ValueError(f"CAST name/hash collision: {name}")
                assets.setdefault(name, {"expected_sha256": digest, "entities": []})["entities"].append(f"{entity}:{view}")
        if len(assets) != 14:
            raise ValueError(f"expected 14 unique CAST files; got {len(assets)}")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return [check("cast_atlas", "FAIL", str(exc), **evidence)]
    checks = [check("cast_atlas", "PASS", "14 unique front/profile hash pins parsed", **evidence, unique_assets=14)]
    for name, pin in sorted(assets.items()):
        path = cast_dir / name
        facts = file_facts(path)
        image = {}
        if facts["exists"]:
            try:
                with Image.open(path) as im:
                    image = {"format": im.format, "size": list(im.size), "mode": im.mode}
                    im.verify()
                with Image.open(path) as im:
                    im.load()
                image["decoded"] = True
            except Exception as exc:
                image["decoded"] = False
                image["error"] = str(exc)
        good = (
            facts["sha256"] == pin["expected_sha256"]
            and isinstance(facts["bytes"], int) and facts["bytes"] >= minimum_bytes
            and image.get("decoded") is True and image.get("format") == "PNG"
            and all(x >= 32 for x in image.get("size", []))
        )
        checks.append(check(f"cast:{name}", "PASS" if good else "FAIL", "CAST bytes and PNG decode" if good else "missing, changed, tiny, or undecodable CAST", file=facts, expected_sha256=pin["expected_sha256"], entities=pin["entities"], image=image, minimum_bytes=minimum_bytes))
    return checks


def literal_assignments(path: Path) -> tuple[dict, dict]:
    facts = file_facts(path)
    if not facts["exists"]:
        return {}, facts
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                continue
            if isinstance(target, ast.Name):
                values[target.id] = value
            elif isinstance(target, ast.Tuple) and isinstance(value, tuple):
                for name, item in zip(target.elts, value):
                    if isinstance(name, ast.Name):
                        values[name.id] = item
    return values, facts


def check_r6_contract(pilot: Path) -> list[dict]:
    common = pilot / "task/corrections/identity/r6/scripts/r6_common.py"
    try:
        values, facts = literal_assignments(common)
        shape = values.get("FPS") == 30.0 and values.get("SPAN_A") == SPAN_A and values.get("SPAN_B") == SPAN_B
        base = values.get("BASE")
        envpy = values.get("ENVPY")
        return [
            check("r6_timebase", "PASS" if shape else "FAIL", "R6 source constants match 300-second contract" if shape else "R6 timebase differs", file=facts, parsed={k: values.get(k) for k in ("FPS", "SPAN_A", "SPAN_B")}),
            check("r6_runtime_paths", "PASS" if base and envpy else "FAIL", "R6 endpoint and Python declarations parsed" if base and envpy else "R6 declarations missing", file=facts, base=base, envpy=envpy),
        ]
    except (OSError, SyntaxError, UnicodeError) as exc:
        return [check("r6_timebase", "FAIL", str(exc), path=str(common)), check("r6_runtime_paths", "UNKNOWN", str(exc), path=str(common))]


def check_availability(pilot: Path) -> list[dict]:
    task = pilot / "task"
    r6 = task / "corrections/identity/r6"
    names = {
        "pilot_input": task / "input",
        "r6_ledger": r6 / "source_actor_ledger.jsonl",
        "r6_atlas": r6 / "cast_atlas.json",
        "r6_storyboard": r6 / "storyboard",
        "r5_storyboard": task / "corrections/identity/r5/storyboard",
        "graph_template": task / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json",
        "r4_cast_dir": task / "corrections/identity/r4/assets/cast_b",
        "r4_sam2_large": task / "corrections/identity/r4/models/sam2.1_hiera_large.pt",
        "r5_cotracker": task / "corrections/identity/r5/models/co-tracker/scaled_offline.pth",
    }
    checks = []
    for label, path in names.items():
        if label in ("pilot_input", "r6_storyboard", "r5_storyboard", "r4_cast_dir"):
            exists = path.is_dir()
            entries = sorted(x.name for x in path.iterdir()) if exists else []
            if label in ("r6_storyboard", "r5_storyboard"):
                expected = [f"{shot}.json" for shot in EXPECTED_SHOTS]
                good = exists and all((path / name).is_file() for name in expected)
                reason = "54 per-shot storyboard files present" if good else "required per-shot storyboard unavailable"
                checks.append(check(label, "PASS" if good else "FAIL", reason, path=str(path), exists=exists, entry_count=len(entries), missing=sorted(set(expected)-set(entries))))
            else:
                good = exists and bool(entries)
                checks.append(check(label, "PASS" if good else "FAIL", "directory contains inputs" if good else "directory absent or empty", path=str(path), exists=exists, entry_count=len(entries)))
        else:
            facts = file_facts(path)
            good = facts["exists"] and facts["bytes"] > 0
            checks.append(check(label, "PASS" if good else "FAIL", "file present and hashed" if good else "required file absent or empty", file=facts))
    historical = file_facts(HISTORICAL_LEDGER)
    checks.append(check("historical_ledger_reference", "PASS" if historical["exists"] else "UNKNOWN", "read-only historical reference; pilot ledger remains independent", file=historical))
    return checks


def check_runtime_python(path: Path) -> dict:
    facts = file_facts(path, full_hash=False)
    if not facts["exists"]:
        return check("runtime_python", "FAIL", "declared runtime Python absent", file=facts, command=None, exit_code=None)
    command = [str(path), "-B", "-c", "import PIL, torch, aiohttp; print('imports-ok')"]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=25, env=env, check=False)
        return check("runtime_python", "PASS" if run.returncode == 0 else "FAIL", "runtime dependency import smoke test", file=facts, command=command, exit_code=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return check("runtime_python", "UNKNOWN", str(exc), file=facts, command=command, exit_code=None)


WEIGHTS = (
    "models/diffusion_models/flux-2-klein-4b-fp8.safetensors",
    "models/vae/flux2-vae.safetensors",
    "models/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors",
    "models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "models/vae/Wan2_1_VAE_bf16.safetensors",
)


def safetensors_header(path: Path) -> dict:
    with path.open("rb") as stream:
        head = stream.read(8)
        if len(head) != 8:
            raise ValueError("truncated safetensors length")
        length = int.from_bytes(head, "little")
        if length < 2 or length > 100_000_000 or length + 8 >= path.stat().st_size:
            raise ValueError("invalid safetensors header length")
        header = json.loads(stream.read(length))
        if not isinstance(header, dict) or not header:
            raise ValueError("empty safetensors header")
        return {"header_bytes": length, "entries": len(header)}


def check_weights(runtime: Path, *, full_hash: bool = True) -> list[dict]:
    checks = []
    for relative in WEIGHTS:
        path = runtime / relative
        facts = file_facts(path, full_hash=full_hash)
        header = None
        error = None
        if facts["exists"]:
            try:
                header = safetensors_header(path)
            except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
                error = str(exc)
        good = facts["exists"] and facts["bytes"] > 1024 and header is not None
        checks.append(check(f"weight:{relative}", "PASS" if good else "FAIL", "file and safetensors header present; loadability untested" if good else "weight missing or invalid header", file=facts, header=header, error=error, model_loadability="UNKNOWN"))
    return checks


def check_runtime_code(runtime: Path, pilot: Path) -> list[dict]:
    main = runtime / "ComfyUI/main.py"
    server = runtime / "tools/serve_video14b.py"
    checks = []
    for label, path in (("comfyui_code", main), ("historical_server_code", server)):
        facts = file_facts(path)
        try:
            if facts["exists"]:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            good = facts["exists"]
            checks.append(check(label, "PASS" if good else "FAIL", "Python source exists and parses; imports untested" if good else "source absent", file=facts, import_status="UNKNOWN"))
        except (OSError, SyntaxError, UnicodeError) as exc:
            checks.append(check(label, "FAIL", str(exc), file=facts))
    common = pilot / "task/corrections/identity/r6/scripts/r6_common.py"
    try:
        values, common_facts = literal_assignments(common)
        server_text = server.read_text(encoding="utf-8")
        match = re.search(r"--port[^\n]*default=(\d+)", server_text)
        default_port = int(match.group(1)) if match else None
        base = values.get("BASE")
        mismatch = base == "http://127.0.0.1:8188" and default_port == 8210
        checks.append(check("endpoint_configuration", "FAIL" if mismatch else "UNKNOWN", "R6 targets 8188; historical server defaults to 8210" if mismatch else "endpoint alignment unverified", r6_common=common_facts, historical_server=file_facts(server), r6_base=base, historical_default_port=default_port))
    except (OSError, SyntaxError, UnicodeError) as exc:
        checks.append(check("endpoint_configuration", "UNKNOWN", str(exc), paths=[str(common), str(server)]))
    runtime_python = check_runtime_python(runtime / "venv/Scripts/python.exe")
    checks.append(runtime_python)
    checks.append(check("runtime_imports", "PASS" if runtime_python["status"] == "PASS" else "UNKNOWN", "declared runtime Python import smoke succeeded" if runtime_python["status"] == "PASS" else "cannot validate runtime imports without declared Python", python_check=runtime_python["id"], command=runtime_python["evidence"].get("command"), exit_code=runtime_python["evidence"].get("exit_code")))
    return checks


def read_endpoint(url: str, check_id: str) -> dict:
    port = int(url.split(":", 2)[2].split("/", 1)[0])
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
    except OSError as exc:
        return check(check_id, "UNKNOWN", "loopback TCP port unavailable; HTTP GET not attempted: " + str(exc), url=url, method="GET", proxy="disabled", socket_command=f"create_connection(127.0.0.1,{port},timeout=2)", socket_exit_code=getattr(exc, "winerror", None) or getattr(exc, "errno", None), http_status=None)
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with direct_opener.open(request, timeout=2) as response:
            data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError("response exceeds 2MB bound")
            status = response.status
        parsed = json.loads(data)
        good = status == 200 and isinstance(parsed, (dict, list))
        return check(check_id, "PASS" if good else "UNKNOWN", "read-only direct HTTP GET response" if good else "unexpected endpoint response", url=url, method="GET", proxy="disabled", http_status=status, response_bytes=len(data), response_sha256=hashlib.sha256(data).hexdigest(), response_json_type=type(parsed).__name__)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return check(check_id, "UNKNOWN", "endpoint unavailable or invalid: " + str(exc), url=url, method="GET", proxy="disabled", http_status=None, exit_code=None)


def check_endpoints() -> list[dict]:
    return [
        read_endpoint("http://127.0.0.1:8188/system_stats", "comfyui_endpoint_8188"),
        read_endpoint("http://127.0.0.1:8188/object_info", "node_api_8188"),
        read_endpoint("http://127.0.0.1:8188/queue", "queue_8188"),
        read_endpoint("http://127.0.0.1:8210/system_stats", "historical_endpoint_8210"),
    ]


def check_process_lease(runtime: Path) -> list[dict]:
    checks = []
    try:
        import psutil
        matches = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or [])
                if any(token in cmd.lower() for token in ("comfyui", "serve_video14b", "video14b")):
                    matches.append({"pid": proc.info["pid"], "name": proc.info.get("name"), "cmdline": cmd[:1000]})
            except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                continue
        checks.append(check("process_snapshot", "PASS", "read-only process inventory only; ownership unresolved", matches=matches, command="psutil.process_iter", exit_code=0))
    except (ImportError, OSError) as exc:
        checks.append(check("process_snapshot", "UNKNOWN", str(exc), command="psutil.process_iter", exit_code=None))
    leases = runtime / "leases"
    reservations = runtime / "reservations"
    files = sorted(leases.glob("*.lease")) if leases.is_dir() else []
    rows = []
    for path in files:
        facts = file_facts(path)
        try:
            data = read_json(path)
            pid = data.get("pid")
            try:
                import psutil
                pid_alive = psutil.pid_exists(pid) if type(pid) is int else None
            except (ImportError, OSError):
                pid_alive = None
            rows.append({"file": facts, "pid": pid, "pid_alive_snapshot": pid_alive, "acquired_at": data.get("acquired_at"), "owner": data.get("owner")})
        except (OSError, ValueError, UnicodeError) as exc:
            rows.append({"file": facts, "error": str(exc)})
    reservation_rows = []
    for path in sorted(reservations.glob("*.json")) if reservations.is_dir() else []:
        try:
            data = read_json(path)
            if data.get("state") == "unresolved":
                server_pid = data.get("server_pid")
                try:
                    import psutil
                    pid_alive = psutil.pid_exists(server_pid) if type(server_pid) is int else None
                except (ImportError, OSError):
                    pid_alive = None
                reservation_rows.append({"file": file_facts(path), "state": "unresolved", "server_pid": server_pid, "server_pid_alive_snapshot": pid_alive, "base_url": data.get("base_url")})
        except (OSError, ValueError, UnicodeError):
            continue
    checks.append(check("lease_ownership", "UNKNOWN", "lease presence and PID snapshot do not establish current ownership; controller audit required", lease_dir=str(leases), leases=rows, unresolved_reservations=reservation_rows, gpu_stage_lock=file_facts(leases / "gpu_stage.lock", full_hash=False)))
    return checks


def run_actual(pilot: Path = PILOT, runtime: Path = RUNTIME) -> dict:
    checks = check_authority()
    checks += [check_manifest_tree(C16, MANIFEST_SHA, None, expected_declared=74, check_id="frozen_c16_bytes")]
    checks += [check_manifest_tree(pilot, MANIFEST_SHA, (SOURCE_BYTES, SOURCE_SHA), expected_declared=74)]
    checks += [check_source_probe(pilot / SOURCE_REL), check_plan(pilot / PLAN_REL)]
    checks += check_r6_contract(pilot)
    checks += check_cast(ATLAS, ATLAS_SHA, pilot / "task/corrections/identity/r4/assets/cast_b")
    checks += check_availability(pilot)
    checks += check_runtime_code(runtime, pilot)
    checks += check_weights(runtime)
    checks.append(check("model_loadability", "UNKNOWN", "weights have headers and hashes, but no runtime import or model load is permitted in this preflight", command=None, exit_code=None))
    checks += check_endpoints()
    checks += check_process_lease(runtime)
    counts = {status: sum(c["status"] == status for c in checks) for status in ("PASS", "FAIL", "UNKNOWN")}
    status = "BLOCKED" if counts["FAIL"] else "UNKNOWN" if counts["UNKNOWN"] else "READY_FOR_ROOT_REVIEW"
    return {"task": "G2-B1-PREFLIGHT-01", "created_utc": utc(), "status": status, "execution": "READ_ONLY_CPU", "pilot": str(pilot), "runtime": str(runtime), "pins": {"manifest_sha256": MANIFEST_SHA, "source_sha256": SOURCE_SHA, "source_bytes": SOURCE_BYTES, "atlas_sha256": ATLAS_SHA, "transport_receipt_sha256": RECEIPT_SHA, "root_review_sha256": ROOT_REVIEW_SHA}, "pilot_contract": {"span_frames": [SPAN_A, SPAN_B], "fps": FPS, "duration_seconds": 300, "shots": [EXPECTED_SHOTS[0], EXPECTED_SHOTS[-1]], "last_shot_is_partial": True}, "checks": checks, "counts": counts, "g2_pilot": "NOT_RUN", "media_render": "NOT_RUN", "model_inference": "NOT_RUN"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve(strict=False)
    root = WRITE_ROOT.resolve(strict=True)
    if target.parent != root or target.exists():
        parser.error(f"output must be a new direct child of {root}")
    result = run_actual()
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(target), "status": result["status"], "counts": result["counts"]}))
    return 0 if result["status"] == "READY_FOR_ROOT_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
