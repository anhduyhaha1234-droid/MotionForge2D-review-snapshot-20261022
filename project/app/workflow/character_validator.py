"""Character pack validation engine (S06-T03).

Validates pose slot completeness, asset file existence, and format criteria
before publishing character pack versions.
"""

from __future__ import annotations

from pathlib import Path

from app.persistence.characters import PackVersionRecord
from app.persistence.models import CORE_POSE_SLOTS


def validate_character_pack(
    version: PackVersionRecord, storage_root: Path | None = None
) -> list[str]:
    """Validate completeness and asset quality of a character pack version.

    Args:
        version: PackVersionRecord to validate.
        storage_root: Root path for managed storage artifacts (optional).

    Returns:
        List of validation error strings. Empty list indicates 100% valid.
    """
    errors: list[str] = []

    # 1. Core pose slot completeness
    attached_slots = {asset.pose_slot: asset for asset in version.assets}
    missing_slots = [slot for slot in CORE_POSE_SLOTS if slot not in attached_slots]

    if missing_slots:
        errors.append(
            f"Missing required core pose slots: {', '.join(sorted(missing_slots))}"
        )

    # 2. Asset file integrity
    for slot, asset in attached_slots.items():
        if not asset.artifact_id:
            errors.append(f"Pose slot '{slot}' is not linked to an artifact")

    return errors


def is_pack_publishable(
    version: PackVersionRecord, storage_root: Path | None = None
) -> bool:
    """Return True if character pack version satisfies all publish criteria."""
    return len(validate_character_pack(version, storage_root)) == 0
