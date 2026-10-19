"""Reference sidecar validation, not a media/quality/approval validator."""
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}\Z")
MODES = {"source_locked", "launch", "footage_edit", "explainer"}
ACTIONS = {"marker", "caption", "graphic", "cut", "retime", "camera"}
CLOCKS = {"source_event", "word", "beat", "storyboard"}


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def validate(plan):
    """Return explicit structural/policy errors; perform no IO or mutations."""
    errors = []
    if not isinstance(plan, dict):
        return ["PLAN_OBJECT_REQUIRED"]
    required = {"schema_version", "mode", "source_sha256", "fps_num", "fps_den",
                "source_start_frame", "source_end_frame", "output_frame_count",
                "audio_policy", "frame_map_policy", "cues"}
    if set(plan) != required:
        errors.append("PLAN_FIELDS_MISMATCH")
    if plan.get("schema_version") != "motionforge.cue-plan/v0.1":
        errors.append("SCHEMA_VERSION_UNSUPPORTED")
    mode = plan.get("mode")
    if not isinstance(mode, str) or mode not in MODES:
        errors.append("MODE_INVALID")
    source_hash = plan.get("source_sha256")
    if not isinstance(source_hash, str) or not SHA.fullmatch(source_hash):
        errors.append("SOURCE_HASH_INVALID")
    for field in ("fps_num", "fps_den", "output_frame_count"):
        if not integer(plan.get(field), 1):
            errors.append(field.upper() + "_INVALID")
    start, end = plan.get("source_start_frame"), plan.get("source_end_frame")
    span_valid = integer(start) and integer(end, 1) and end > start
    if not span_valid:
        errors.append("SOURCE_SPAN_INVALID")
    frame_map = plan.get("frame_map_policy")
    audio = plan.get("audio_policy")
    if frame_map not in ("identity", "explicit_edl", "authored"):
        errors.append("FRAME_MAP_POLICY_INVALID")
    if audio not in ("original_locked", "authored_mix", "edl_mapped"):
        errors.append("AUDIO_POLICY_INVALID")
    if mode == "source_locked":
        if frame_map != "identity" or audio != "original_locked":
            errors.append("SOURCE_LOCK_POLICY_VIOLATION")
        if span_valid and plan.get("output_frame_count") != end - start:
            errors.append("SOURCE_LOCK_FRAME_COUNT_MISMATCH")
    if mode == "footage_edit" and (frame_map != "explicit_edl" or audio != "edl_mapped"):
        errors.append("EDIT_MAP_REQUIRED")
    cues = plan.get("cues")
    if not isinstance(cues, list):
        return errors + ["CUES_ARRAY_REQUIRED"]
    seen = set()
    for index, cue in enumerate(cues):
        prefix = f"CUE[{index}]:"
        def fail(code):
            errors.append(prefix + code)
        if not isinstance(cue, dict):
            fail("OBJECT_REQUIRED")
            continue
        if set(cue) != {"id", "start_frame", "end_frame", "clock", "action", "evidence"}:
            fail("FIELDS_MISMATCH")
        cue_id = cue.get("id")
        if not isinstance(cue_id, str) or not cue_id.strip():
            fail("ID_INVALID")
        elif cue_id in seen:
            fail("ID_DUPLICATE")
        else:
            seen.add(cue_id)
        a, b, count = cue.get("start_frame"), cue.get("end_frame"), plan.get("output_frame_count")
        if not (integer(a) and integer(b, 1) and integer(count, 1) and a < b <= count):
            fail("FRAME_RANGE_INVALID")
        action, clock = cue.get("action"), cue.get("clock")
        if not isinstance(action, str) or action not in ACTIONS:
            fail("ACTION_INVALID")
        if not isinstance(clock, str) or clock not in CLOCKS:
            fail("CLOCK_INVALID")
        if mode == "source_locked" and action != "marker":
            fail("SOURCE_LOCK_MUTATION_FORBIDDEN")
        evidence = cue.get("evidence")
        if not isinstance(evidence, dict):
            fail("EVIDENCE_REQUIRED")
            continue
        if set(evidence) != {"asset_sha256", "record_id", "timing_method"}:
            fail("EVIDENCE_FIELDS_MISMATCH")
        digest = evidence.get("asset_sha256")
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            fail("EVIDENCE_HASH_INVALID")
        if not isinstance(evidence.get("record_id"), str) or not evidence["record_id"].strip():
            fail("EVIDENCE_RECORD_REQUIRED")
        method = evidence.get("timing_method")
        if method not in ("measured", "estimated", "authored"):
            fail("TIMING_METHOD_INVALID")
        if clock == "word" and method != "measured":
            fail("WORD_TIMING_NOT_MEASURED")
        if clock == "source_event" and digest != source_hash:
            fail("SOURCE_EVENT_HASH_MISMATCH")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_cues.py <plan.json>", file=sys.stderr)
        return 2
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        errors = validate(plan)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"contract_valid": False, "input_error": str(exc)}))
        return 2
    print(json.dumps({"contract_valid": not errors, "errors": errors,
                      "media_verified": False, "quality_accepted": False}))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
