"""R6 Canonical Event Contract — unified parsing of timing, bounds, contacts and transitions.

Consistently handles:
- 0-based 'f' vs 1-based 'frame'
- Strict integer types and bounds [1, n]
- Detection of conflicting 'f' vs 'frame'
- Full state transitions: entry, exit, occlusion, reappear, contact start and contact end
"""
from __future__ import annotations
from typing import Any


def parse_event_fid(e: dict[str, Any], n: int, sid: str = "") -> int:
    """Extract and validate 1-based fid from an event record."""
    if not isinstance(e, dict):
        raise ValueError(f"event record must be a dict in {sid}: {e}")
    f_val = e.get("f")
    frame_val = e.get("frame")
    if f_val is not None and frame_val is not None:
        if int(f_val) + 1 != int(frame_val):
            raise ValueError(f"conflicting event f ({f_val}) vs frame ({frame_val}) in {sid}")
    if frame_val is not None:
        fid = int(frame_val)
    elif f_val is not None:
        fid = int(f_val) + 1
    else:
        raise ValueError(f"event record missing both 'f' and 'frame' in {sid}: {e}")
    if fid < 1 or fid > n:
        raise ValueError(f"event fid {fid} out of range [1, {n}] in {sid}")
    return fid


def parse_contact_fids(c: dict[str, Any], n: int, sid: str = "") -> tuple[int, int | None]:
    """Extract and validate contact start (from+1) and end (to) fids."""
    if not isinstance(c, dict):
        raise ValueError(f"contact record must be a dict in {sid}: {c}")
    if "from" not in c:
        raise ValueError(f"contact record missing 'from' in {sid}: {c}")
    from_raw = int(c["from"])
    fid_from = from_raw + 1
    if fid_from < 1 or fid_from > n:
        raise ValueError(f"contact from={from_raw} (fid={fid_from}) out of range [1, {n}] in {sid}")
    
    fid_to = None
    if "to" in c:
        to_raw = int(c["to"])
        fid_to = to_raw
        if fid_to < 1 or fid_to > n:
            raise ValueError(f"contact to={to_raw} out of range [1, {n}] in {sid}")
        if fid_to < fid_from:
            raise ValueError(f"contact to ({fid_to}) < from ({fid_from}) in {sid}")
    return fid_from, fid_to


def extract_canonical_event_fids(row: dict[str, Any], sid: str = "") -> set[int]:
    """Extract all canonical event fids for a shot ledger row."""
    n = int(row.get("n", 9999))
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
            w_from = int(w.get("from", 0))
            w_to = int(w.get("to", 9999))
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
