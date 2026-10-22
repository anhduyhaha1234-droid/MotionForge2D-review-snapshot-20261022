"""G2-B2 exact-byte recovery vault. CPU-only; never imports R6 or starts media services."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


WRITE_ROOT = Path(r"C:\Users\Admin\Documents\Codex\g2b2-recovery")
PILOT = Path(r"C:\Users\Admin\Documents\Codex\g2p01-transport\pilot-g2p01-001")
PACKET = Path(r"C:\Users\Admin\Documents\Codex\work\mf-portable-handoff-20261019\review_and_handoff\motionforge-r6-checkpoint-review-20261014")
R6_SNAPSHOT = PACKET / "snapshot/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6"
GRAPH_BUNDLE = Path(r"C:\Users\Admin\Documents\Codex\2026-09-22\tr-ng-th-i-terminal-gi\outputs\mf-rebuild-skills-20261001\reuse_bundle")
GRAPH_NAME = "shot_anchor_v1.baseline.api.json"
GRAPH_MIRRORS = (
    Path(r"C:\Users\Admin\Documents\Codex\work\mf-external-review-20260929\docs\external-review\updates\20261002\reuse_bundle") / GRAPH_NAME,
    Path(r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261002\20261002T031500Z-wan-shotwise\tasks\MF-DEMO-E2E-R5\WAN-PROTOTYPE-01\reuse_bundle") / GRAPH_NAME,
)
PILOT_MANIFEST_SHA = "4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82"
PACKET_MANIFEST_SHA = "0f8785bda71c1fd8ea2374da7adc10eee5775eaeb79ad00ceaae586e691ae5e8"
PROVENANCE_SHA = "7b536305b093b10827a5e4732de6ff23057e830e433d2e5b6c209000b82f1971"
ROOT_REVIEW_SHA = "99e2f6b3db28c413bc8eefc6483d75e7ad2a42e5723af45e3e56ca55cb72c0ab"
ROOT_CHECKPOINT_SHA = "a7e24fca7281808917694d73285eb2ef34c0aa6b2d987018962a22ad99e9b484"
SHA = re.compile(r"^[0-9a-f]{64}$")
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


@dataclass(frozen=True)
class Source:
    name: str
    path: Path
    relative: str
    size: int
    sha256: str


SOURCES = (
    Source("ledger", R6_SNAPSHOT / "source_actor_ledger.jsonl", "task/corrections/identity/r6/source_actor_ledger.jsonl", 36876, "1012a20a03b10e91a22e1e7a588e4f6b7f8259599f90f0d4fd855bec9f9c3715"),
    Source("atlas", R6_SNAPSHOT / "cast_atlas.json", "task/corrections/identity/r6/cast_atlas.json", 4120, "e847acb8d30f120bcaffb81b1e5048baf3e32280bcd74e9e5688b20a56149a4e"),
    Source("graph", GRAPH_BUNDLE / GRAPH_NAME, "task/graph/reuse_bundle/shot_anchor_v1.baseline.api.json", 16804, "0ff8ed9c92441230d76d42f2d3eeffb92e70f1b8749f663b170d1566a3df7f4e"),
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def result(name: str, status: str, reason: str, **evidence: object) -> dict:
    assert status in ("PASS", "FAIL", "UNVERIFIED")
    return {"check": name, "status": status, "reason": reason, "evidence": evidence}


def safe_relative(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise ValueError(f"unsafe relative path: {raw!r}")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or pure.as_posix() != raw or any(part in (".", "..", "") or ":" in part for part in pure.parts):
        raise ValueError(f"unsafe relative path: {raw!r}")
    return raw


def no_reparse_ancestor(path: Path) -> None:
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if item.is_symlink() or getattr(info, "st_file_attributes", 0) & REPARSE:
            raise ValueError(f"reparse point in path: {item}")


def facts(path: Path) -> dict:
    record = {"path": str(path), "exists": False, "bytes": None, "sha256": None}
    no_reparse_ancestor(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return record
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"not a regular file: {path}")
    record["exists"] = True
    record["bytes"] = info.st_size
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    record["sha256"] = digest.hexdigest()
    return record


def strict_json(path: Path) -> dict:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key}")
            out[key] = value
        return out
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def validate_specs(specs: tuple[Source, ...]) -> list[dict]:
    if len(specs) != 3 or {s.name for s in specs} != {"ledger", "atlas", "graph"}:
        raise ValueError("exactly ledger, atlas, graph are required")
    paths = set()
    names = set()
    checks = []
    for source in specs:
        rel = safe_relative(source.relative)
        if rel.casefold() in paths or source.name.casefold() in names:
            raise ValueError(f"duplicate destination/name: {rel}")
        paths.add(rel.casefold())
        names.add(source.name.casefold())
        if type(source.size) is not int or source.size < 1 or not SHA.fullmatch(source.sha256):
            raise ValueError(f"invalid source pin: {source.name}")
        actual = facts(source.path)
        good = actual["bytes"] == source.size and actual["sha256"] == source.sha256
        checks.append(result("source:" + source.name, "PASS" if good else "FAIL", "exact source bytes" if good else "source absent or pin mismatch", source=actual, expected_bytes=source.size, expected_sha256=source.sha256, vault_relative=rel))
    return checks


def authority_checks() -> list[dict]:
    checks = []
    pins = (
        ("root_review", Path(r"C:\Users\Admin\Documents\Codex\g2-readiness-audit\ROOT_REVIEW_G2B1.md"), ROOT_REVIEW_SHA),
        ("root_checkpoint", Path(r"C:\Users\Admin\Documents\Codex\g2-readiness-audit\CHECKPOINT.json"), ROOT_CHECKPOINT_SHA),
        ("packet_manifest", PACKET / "PACKET_MANIFEST.json", PACKET_MANIFEST_SHA),
        ("graph_provenance", GRAPH_BUNDLE / "PROVENANCE.json", PROVENANCE_SHA),
        ("pilot_manifest", PILOT / "MANIFEST.json", PILOT_MANIFEST_SHA),
    )
    for name, path, pin in pins:
        actual = facts(path)
        checks.append(result(name, "PASS" if actual["sha256"] == pin else "FAIL", "authority SHA-256", file=actual, expected_sha256=pin))
    if any(row["status"] == "FAIL" for row in checks):
        return checks
    manifest = strict_json(PACKET / "PACKET_MANIFEST.json")
    rows = manifest["files"]
    for source in SOURCES[:2]:
        rel = str(source.path.relative_to(PACKET)).replace("/", "\\")
        matches = [row for row in rows if row.get("path", "").casefold() == rel.casefold()]
        good = len(matches) == 1 and matches[0].get("bytes") == source.size and matches[0].get("sha256") == source.sha256
        checks.append(result("packet_lineage:" + source.name, "PASS" if good else "FAIL", "packet manifest matches exact R6 snapshot file", manifest=str(PACKET / "PACKET_MANIFEST.json"), relative=rel, rows=matches))
    provenance = strict_json(GRAPH_BUNDLE / "PROVENANCE.json")
    entries = [row for row in provenance["files"] if row.get("api_graph") == str(SOURCES[2].path)]
    good = len(entries) == 1 and entries[0].get("api_sha256") == SOURCES[2].sha256 and entries[0].get("nodes") == 48
    checks.append(result("graph_lineage_record", "PASS" if good else "FAIL", "PROVENANCE graph binding", provenance=str(GRAPH_BUNDLE / "PROVENANCE.json"), entries=entries))
    if good:
        entry = entries[0]
        for label, key, pin_key in (("wrapper_original", "source", "source_sha256"), ("wrapper_snapshot", "snapshot", "snapshot_sha256")):
            record = facts(Path(entry[key]))
            checks.append(result(label, "PASS" if record["sha256"] == entry[pin_key] else "FAIL", "wrapper provenance bytes", file=record, expected_sha256=entry[pin_key]))
    for i, mirror in enumerate(GRAPH_MIRRORS, 1):
        record = facts(mirror)
        checks.append(result(f"graph_mirror_{i}", "PASS" if record["bytes"] == 16804 and record["sha256"] == SOURCES[2].sha256 else "FAIL", "independent historical graph copy", file=record, expected_sha256=SOURCES[2].sha256))
    pilot_manifest = strict_json(PILOT / "MANIFEST.json")
    for name in ("r6_graph.py", "r6_key_recipe.py", "r6_ledger.py"):
        rel = "task/corrections/identity/r6/scripts/" + name
        records = [row for row in pilot_manifest["files"] if row.get("relative") == rel]
        record = facts(PILOT / rel)
        good = len(records) == 1 and records[0].get("bytes") == record["bytes"] and records[0].get("sha256") == record["sha256"]
        checks.append(result("historical_code:" + name, "PASS" if good else "FAIL", "approved pilot manifest pins historical R6 code", file=record, manifest_row=records))
    return checks


def validate_ledger_atlas(ledger_path: Path, atlas_path: Path) -> list[dict]:
    checks = []
    try:
        rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
        ids = [f"S{i:04d}" for i in range(21, 75)]
        cursor = 2820
        for shot, row in zip(ids, rows):
            start, end = row["src"]
            if row["shot"] != shot or start != cursor or type(end) is not int or end <= start or row["n"] != end - start or row["fps"] != 30.0:
                raise ValueError(f"ledger span mismatch: {shot}")
            cursor = end
        if len(rows) != 54 or cursor != 11980:
            raise ValueError("ledger shot count or final frame mismatch")
        checks.append(result("ledger_structure", "PASS", "54 contiguous source-shot rows", path=str(ledger_path), rows=len(rows), span=[2820, cursor], first=rows[0]["shot"], last=rows[-1]["shot"]))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [result("ledger_structure", "FAIL", str(exc), path=str(ledger_path))]
    try:
        atlas = strict_json(atlas_path)
        entities = atlas["entities"]
        assets = {}
        for entity, row in entities.items():
            for view in ("front", "profile"):
                item = row[view]
                filename, digest = item["file"], item["sha256"]
                if not isinstance(filename, str) or filename != Path(filename).name or ":" in filename or not filename.endswith(".png") or not SHA.fullmatch(digest):
                    raise ValueError(f"invalid CAST pin {entity}:{view}")
                if filename in assets and assets[filename] != digest:
                    raise ValueError(f"CAST filename collision {filename}")
                assets[filename] = digest
        if len(assets) != 14:
            raise ValueError(f"expected 14 CAST filenames, found {len(assets)}")
        used = {actor["cast"] for row in rows for actor in row["actors"]}
        if not used.issubset(assets):
            raise ValueError("ledger refers to CAST file absent from atlas")
        checks.append(result("atlas_ledger_structure", "PASS", "14 unique CAST pins; ledger names bind atlas", path=str(atlas_path), unique_cast_pins=len(assets), used_fronts=sorted(used), cast_png_bytes="NOT_STAGED"))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        checks.append(result("atlas_ledger_structure", "FAIL", str(exc), path=str(atlas_path)))
    return checks


def links(node: dict) -> list[str]:
    return [value[0] for value in node.get("inputs", {}).values() if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and type(value[1]) is int]


def reachable(graph: dict, start: str) -> set[str]:
    seen, pending = set(), [start]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(links(graph[node]))
    return seen


def validate_graph(path: Path, r6_graph_code: Path, r6_recipe_code: Path) -> list[dict]:
    try:
        graph = strict_json(path)
        ast.parse(r6_graph_code.read_text(encoding="utf-8"))
        ast.parse(r6_recipe_code.read_text(encoding="utf-8"))
        graph_source = r6_graph_code.read_text(encoding="utf-8")
        recipe_source = r6_recipe_code.read_text(encoding="utf-8")
        required = {"UNET", "CLIP", "VAE", "SIGMAS", "SAMPLER", "GUIDER", "NOISE", "LATENT", "KEY_LOAD", "R1_LOAD", "R2_LOAD", "R3_LOAD", "R2_POS", "R2_NEG", "SAVE"}
        if len(graph) != 48 or not required.issubset(graph):
            raise ValueError("graph node count or IDs do not match historical R6 contract")
        if any(not isinstance(node, dict) or not isinstance(node.get("class_type"), str) or not isinstance(node.get("inputs"), dict) for node in graph.values()):
            raise ValueError("graph node schema invalid")
        unresolved = sorted({target for node in graph.values() for target in links(node) if target not in graph})
        if unresolved:
            raise ValueError(f"unresolved graph node links: {unresolved}")
        if (graph["UNET"]["inputs"].get("unet_name") != "flux-2-klein-4b-fp8.safetensors"
                or graph["CLIP"]["inputs"].get("clip_name") != "qwen_3_4b.safetensors"
                or graph["VAE"]["inputs"].get("vae_name") != "flux2-vae.safetensors"
                or graph["SIGMAS"]["inputs"].get("steps") != 4
                or graph["SAMPLER"]["inputs"].get("sampler_name") != "euler"
                or graph["GUIDER"]["inputs"].get("cfg") != 1.0):
            raise ValueError("FLUX.2 distilled baseline settings differ")
        if ('shot_anchor_v1.baseline.api.json' not in graph_source
                or 'g["GUIDER"]["inputs"]["positive"] = ["R2_POS", 0]' not in graph_source
                or 'g["GUIDER"]["inputs"]["negative"] = ["R2_NEG", 0]' not in graph_source
                or 'graph = _strict_json(G.TPL)' not in recipe_source):
            raise ValueError("historical R6 template binding or rewire differs")
        # Simulate only the R6 conditioning rewire; never write or execute graph.
        graph["GUIDER"]["inputs"]["positive"] = ["R2_POS", 0]
        graph["GUIDER"]["inputs"]["negative"] = ["R2_NEG", 0]
        used = reachable(graph, "R2_POS") | reachable(graph, "R2_NEG")
        if not {"KEY_LOAD", "R1_LOAD", "R2_LOAD"}.issubset(used) or "R3_LOAD" in used:
            raise ValueError("R6 CAST/key conditioning reachability differs")
        return [
            result("graph_static_schema", "PASS", "48 nodes, links, baseline settings and R6 rewire pass static checks", file=facts(path), nodes=len(graph), refs_reachable=sorted({"KEY_LOAD", "R1_LOAD", "R2_LOAD"} & used), r3_reachable=False, model_names={"unet": graph["UNET"]["inputs"]["unet_name"], "clip": graph["CLIP"]["inputs"]["clip_name"], "vae": graph["VAE"]["inputs"]["vae_name"]}),
            result("graph_runtime_compatibility", "UNVERIFIED", "no node API, graph execution, model load or inference in this task", template=str(path), process_exit_code=None),
        ]
    except (OSError, KeyError, TypeError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        return [result("graph_static_schema", "FAIL", str(exc), path=str(path)), result("graph_runtime_compatibility", "UNVERIFIED", "static schema failed; runtime not attempted", path=str(path))]


def recover(vault: Path, specs: tuple[Source, ...] = SOURCES, *, use_authority: bool = True) -> dict:
    receipt = {"task": "G2-B2-RECOVER-01", "created_utc": now(), "status": "BLOCKED", "vault": str(vault), "checks": [], "copied": [], "g2_media": "BLOCKED", "render": "NOT_RUN", "inference": "NOT_RUN"}
    checks = receipt["checks"]
    try:
        if use_authority and specs != SOURCES:
            raise ValueError("authoritative recovery requires the exact three pinned sources")
        no_reparse_ancestor(vault)
        if vault.exists():
            raise ValueError(f"vault exists; refusing overwrite: {vault}")
        checks.extend(validate_specs(specs))
        if any(row["status"] == "FAIL" for row in checks):
            return receipt
        if use_authority:
            checks.extend(authority_checks())
            if any(row["status"] == "FAIL" for row in checks):
                return receipt
            by_name = {source.name: source for source in specs}
            checks.extend(validate_ledger_atlas(by_name["ledger"].path, by_name["atlas"].path))
            checks.extend(validate_graph(by_name["graph"].path, PILOT / "task/corrections/identity/r6/scripts/r6_graph.py", PILOT / "task/corrections/identity/r6/scripts/r6_key_recipe.py"))
            if any(row["status"] == "FAIL" for row in checks):
                return receipt
        vault.mkdir(parents=False, exist_ok=False)
        for source in specs:
            destination = vault / source.relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.path.open("rb") as inp, destination.open("xb") as out:
                for block in iter(lambda: inp.read(1024 * 1024), b""):
                    out.write(block)
            post = facts(destination)
            good = post["bytes"] == source.size and post["sha256"] == source.sha256
            checks.append(result("postimage:" + source.name, "PASS" if good else "FAIL", "copied bytes match pin" if good else "postimage differs", file=post, source=str(source.path), expected_bytes=source.size, expected_sha256=source.sha256))
            receipt["copied"].append(post)
        actual = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*") if path.is_file())
        expected = sorted(source.relative for source in specs)
        exact = actual == expected and not any(row["status"] == "FAIL" for row in checks)
        checks.append(result("vault_inventory", "PASS" if exact else "FAIL", "exact three-file vault inventory" if exact else "vault inventory mismatch", actual=actual, expected=expected))
        receipt["status"] = "SELF_VERIFIED_PENDING_ROOT_REVIEW" if exact else "BLOCKED"
        receipt["verified_utc"] = now()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks.append(result("recovery_operation", "FAIL", str(exc), vault=str(vault)))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=WRITE_ROOT / "vault-g2b2-001")
    parser.add_argument("--receipt", type=Path, default=WRITE_ROOT / "RECEIPT.json")
    args = parser.parse_args()
    write_root = WRITE_ROOT.resolve(strict=True)
    vault = args.vault.resolve(strict=False)
    receipt_path = args.receipt.resolve(strict=False)
    if vault.parent != write_root or receipt_path.parent != write_root or vault == receipt_path or receipt_path.exists():
        parser.error("vault and new receipt must be distinct direct children of the exclusive write-set")
    receipt = recover(vault)
    with receipt_path.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path), "vault": str(vault), "copied": len(receipt["copied"])}, ensure_ascii=False))
    return 0 if receipt["status"] == "SELF_VERIFIED_PENDING_ROOT_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
