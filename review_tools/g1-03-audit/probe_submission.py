"""Isolated candidate03 gate/adapter probes; imports no production configuration."""
from pathlib import Path
import contextlib, hashlib, importlib.util, io, json, os, sys, types

BASE = Path(__file__).resolve().parent
PACKET = BASE.parents[1] / "outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-03"
SOURCE = BASE / "source"
ROOT = BASE / "sandbox/r6"
SOURCE.mkdir(parents=True, exist_ok=True)
ROOT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
want = {"scripts/r6_gate.py", "scripts/r6_matrix.py", "scripts/r6_evidence_contract.py"}
hash_checks = []
for item in manifest["files"]:
    if item["relative"] in want:
        data = Path(item["path"]).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        assert actual == item["sha256"], (item["relative"], actual)
        target = SOURCE / Path(item["relative"]).name
        target.write_bytes(data)
        hash_checks.append({"relative": item["relative"], "sha256": actual, "match": True})
adapter_source = PACKET / "dependencies_snapshot/r6_submission_adapter.py"
adapter_hash = sha(adapter_source)
assert adapter_hash == "19ee08eb9c75dab104130ac1affd158c05b5e6febd335afde09d47e25e57a880"
(SOURCE / adapter_source.name).write_bytes(adapter_source.read_bytes())
hash_checks.append({"relative": "dependencies_snapshot/r6_submission_adapter.py", "sha256": adapter_hash,
                    "match": True, "binding": "packet snapshot; not listed in MANIFEST.files"})

# Production r6_common makes directories at import. Replace configuration only;
# all gate/matrix/evidence/adapter function bodies below are exact candidate bytes.
K = types.ModuleType("r6_common")
K.R6 = ROOT
K.sha = sha
sys.modules["r6_common"] = K
sys.modules["r6_cache"] = types.ModuleType("r6_cache")
def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
G = load("r6_gate")
E = load("r6_evidence_contract")
M = load("r6_matrix")
A = load("r6_submission_adapter")

results = {"hash_checks": hash_checks, "isolation": "Exact source copies; K.R6/K.sha scratch config; unused r6_cache stub; no production imports, models, GPU, or shared writes"}
def rows(final=False):
    return {f"Q{i:02}": {"verdict": "PASS" if final or i in (5, 7) else "UNKNOWN", "evidence": "unverified label"} for i in range(1, 13)}
def verdicts(r): return {k: v["verdict"] for k,v in r.items()}
def put(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")
def capture(call):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: value = call(); error = None
        except Exception as exc: value = None; error = f"{type(exc).__name__}: {exc}"
    return {"returned": value, "error": error, "stdout": out.getvalue(), "stderr": err.getvalue()}

r = rows()
results["engineering_label_only_proof"] = capture(lambda: G.gate_batch_conformance({"matrix": verdicts(r), "proof": {"Q05": {"verdict": "PASS"}, "Q07": {"verdict": "PASS"}}}))
results["engineering_missing_proof_control"] = capture(lambda: G.gate_batch_conformance({"matrix": verdicts(r)}))

ns = ROOT / "continuations/test-adapter"
ns.mkdir(parents=True, exist_ok=True)
os.environ["R6_INVOCATION_DIR"] = str(ns)
put(ns / "R6_MATRIX_EVIDENCE.json", {"rows": r})
artifact = ns / "artifact.bin"
artifact.write_bytes(b"ABCD")
item = {"path": str(artifact.relative_to(ROOT)), "absolute_path": str(artifact), "sha256": sha(artifact), "bytes": 4}
put(ns / "R6G_MANIFEST.json", {"at": "2026-10-19T00:00:00Z", "items": [item]})
results["adapter_engineering_positive"] = capture(lambda: A.validate_and_submit(terminal_path=ns / "terminal-positive.json"))
artifact.write_bytes(b"WXYZ")
results["adapter_same_size_hash_tamper"] = capture(lambda: A.validate_and_submit(terminal_path=ns / "terminal-tampered.json"))
results["adapter_same_size_hash_tamper"].update({"manifest_sha256": item["sha256"], "actual_sha256": sha(artifact), "terminal_published": (ns / "terminal-tampered.json").exists()})
artifact.write_bytes(b"WXYZ!")
results["adapter_size_mismatch_control"] = capture(lambda: A.validate_and_submit(terminal_path=ns / "terminal-size-mismatch.json"))
results["adapter_size_mismatch_control"]["terminal_published"] = (ns / "terminal-size-mismatch.json").exists()

final_items = []
for kind in ("master", "comparison", "matrix", "checkpoint", "receipts"):
    p = ns / f"{kind}.dat"
    p.write_bytes(f"artifact-{kind}".encode())
    final_items.append({"kind": kind, "path": str(p), "absolute_path": str(p), "sha256": sha(p), "bytes": p.stat().st_size})
final_rows = rows(True)
put(ns / "R6_MATRIX_EVIDENCE.json", {"rows": final_rows})
put(ns / "R6G_MANIFEST.json", {"items": final_items})
results["final_gate_valid_artifacts_control"] = capture(lambda: G.gate_batch_conformance({"matrix": verdicts(final_rows), "artifacts": final_items}, mode="final"))
results["adapter_final_same_valid_artifacts"] = capture(lambda: A.validate_and_submit(mode="final", terminal_path=ns / "terminal-final.json"))
results["adapter_final_same_valid_artifacts"]["terminal_published"] = (ns / "terminal-final.json").exists()

stage_ns = ROOT / "continuations/test-stage"
results["stage_empty_manifest_labels"] = capture(lambda: E.stage_and_publish_matrix(r, {"at": "new", "items": []}, stage_ns))
results["stage_empty_manifest_labels"].update({"matrix_published": (stage_ns / "R6_MATRIX_EVIDENCE.json").exists(), "manifest_published": (stage_ns / "R6G_MANIFEST.json").exists()})
put(stage_ns / "R6_MATRIX_EVIDENCE.json", {"at": "old", "rows": r})
old_manifest = M.build_manifest()
E.stage_and_publish_matrix(r, old_manifest, stage_ns)
matrix_item = next(x for x in old_manifest["items"] if x["absolute_path"] == str(stage_ns / "R6_MATRIX_EVIDENCE.json"))
results["manifest_after_publication"] = {"manifest_matrix_sha256": matrix_item["sha256"], "published_matrix_sha256": sha(stage_ns / "R6_MATRIX_EVIDENCE.json"), "matches": matrix_item["sha256"] == sha(stage_ns / "R6_MATRIX_EVIDENCE.json")}

video_ns = ROOT / "continuations/test-matrix"
M.NS = video_ns
fake_video = video_ns / "outputs/R6G_MASTER.mp4"
fake_video.parent.mkdir(parents=True, exist_ok=True)
fake_video.write_bytes(b"ftyp" + b"x" * 99996)
put(video_ns / "receipts/R6G_ASSEMBLY_RECEIPT.json", {"frames": 9000, "master_bytes": 100000})
testfile = video_ns / "tests/test_r6g_microfixes.py"
testfile.parent.mkdir(parents=True, exist_ok=True)
testfile.write_bytes(b"garbage" * 20)
put(video_ns / "receipts/R6_GATE_EVIDENCE.json", {"all_passed": True, "tests_run": 1})
computed = M.compute_rows()
results["non_video_magic_and_labels"] = {"video_validation": E.validate_evidence_video(fake_video, 9000), "Q08": computed["Q08"], "Q05": computed["Q05"], "note": "File is ftyp plus repeated x, not an MP4 container; test is non-Python garbage never executed"}

out = BASE / "PROBE_RESULTS.json"
out.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps({"results": str(out), **results}, indent=2))
