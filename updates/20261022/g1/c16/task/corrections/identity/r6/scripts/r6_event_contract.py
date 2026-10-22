"""R6 Canonical Event Contract — unified parsing of timing, bounds, contacts and transitions.

Consistently handles:
- Strict integer types (rejects float, bool, str coercion)
- 0-based 'f' vs 1-based 'frame'
- Bounds [1, n] for 1-based fids, [0, n-1] for 0-based f
- Detection of conflicting 'f' vs 'frame'
- Full state transitions: entry, exit, occlusion, reappear, contact start and contact end
"""
from __future__ import annotations
from typing import Any


def check_strict_int(val: Any, name: str, sid: str = "") -> int:
    """Validate that val is strictly an int and not a bool, float, str, or other type."""
    if isinstance(val, bool) or type(val) is not int:
        raise ValueError(f"{name} must be a strict integer (got {type(val).__name__}={val!r}) in {sid}")
    return val


def parse_event_fid(e: dict[str, Any], n: int, sid: str = "") -> int:
    """Extract and validate 1-based fid from an event record with strict integer checks."""
    if not isinstance(e, dict):
        raise ValueError(f"event record must be a dict in {sid}: {e}")
    f_val = e.get("f")
    frame_val = e.get("frame")
    
    if f_val is None and frame_val is None:
        raise ValueError(f"event record missing both 'f' and 'frame' in {sid}: {e}")
        
    if f_val is not None:
        f_int = check_strict_int(f_val, "event f", sid)
        if f_int < 0 or f_int >= n:
            raise ValueError(f"event f {f_int} out of range [0, {n-1}] in {sid}")
    else:
        f_int = None
        
    if frame_val is not None:
        frame_int = check_strict_int(frame_val, "event frame", sid)
        if frame_int < 1 or frame_int > n:
            raise ValueError(f"event fid {frame_int} out of range [1, {n}] in {sid}")
    else:
        frame_int = None
        
    if f_int is not None and frame_int is not None:
        if f_int + 1 != frame_int:
            raise ValueError(f"conflicting event f ({f_int}) vs frame ({frame_int}) in {sid}")
            
    fid = frame_int if frame_int is not None else (f_int + 1)
    if fid < 1 or fid > n:
        raise ValueError(f"event fid {fid} out of range [1, {n}] in {sid}")
    return fid


def parse_contact_fids(c: dict[str, Any], n: int, sid: str = "") -> tuple[int, int | None]:
    """Extract and validate contact start (from+1) and end (to) fids with strict integer checks."""
    if not isinstance(c, dict):
        raise ValueError(f"contact record must be a dict in {sid}: {c}")
    if "from" not in c:
        raise ValueError(f"contact record missing 'from' in {sid}: {c}")
    from_raw = check_strict_int(c["from"], "contact from", sid)
    if from_raw < 0:
        raise ValueError(f"contact from={from_raw} out of range [0, {n-1}] in {sid}")
    fid_from = from_raw + 1
    if fid_from < 1 or fid_from > n:
        raise ValueError(f"contact from={from_raw} (fid={fid_from}) out of range [1, {n}] in {sid}")
    
    fid_to = None
    if "to" in c and c["to"] is not None:
        to_raw = check_strict_int(c["to"], "contact to", sid)
        if to_raw < 1 or to_raw > n:
            raise ValueError(f"contact to={to_raw} out of range [1, {n}] in {sid}")
        if to_raw < fid_from:
            raise ValueError(f"contact to ({to_raw}) < from ({fid_from}) in {sid}")
        fid_to = to_raw
    return fid_from, fid_to


def extract_canonical_event_fids(row: dict[str, Any], sid: str = "") -> set[int]:
    """Extract all canonical event fids for a shot ledger row."""
    n = check_strict_int(row.get("n", 9999), "shot frame count n", sid)
    ev: set[int] = set()

    # 1. Discrete events
    for e in row.get("events", []):
        if isinstance(e, dict):
            fid = parse_event_fid(e, n, sid)
            ev.add(fid)

    # 2. Contacts
    for c in row.get("contacts", []):
        if isinstance(c, dict):
            fid_from, fid_to = parse_contact_fids(c, n, sid)
            ev.add(fid_from)
            if fid_to is not None and fid_to <= n:
                ev.add(fid_to)

    # 3. Actor class windows (entry, exit, occlusion, reappear)
    for a in row.get("actors", []):
        for w in a.get("class_windows", []):
            if "from" in w:
                w_from = check_strict_int(w["from"], "window from", sid)
            else:
                w_from = 0
            if "to" in w:
                w_to = check_strict_int(w["to"], "window to", sid)
            else:
                w_to = 9999
            cls = w.get("class", "")
            # Visible or partially visible entry/reappear
            if 1 < w_from <= n and cls in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev.add(w_from)
            # Occlusion or not present entry
            if 1 < w_from <= n and cls in ("FULLY_OCCLUDED", "NOT_PRESENT"):
                ev.add(w_from)
            # End of visible span
            if 1 <= w_to < n and cls in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev.add(w_to + 1)

    return ev
