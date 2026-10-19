"""S03-T04 focused unit tests — pure next-action/count mapping.

These tests exercise the two pure, database-free mapping helpers of the
summary read model:

- ``map_video_status_counts``: exact active/archived/total/completed/
  attention counts and the zero-filled 13-status ``by_status`` map
  (AC3 — no join inflation, zeroes included).
- ``determine_next_action``: deterministic state-driven semantic action
  codes with the correct Video Item id, enabled/blocker semantics and
  capability-honest ``none`` (AC4).

The database-backed repository/route behavior is covered by the S03-T04
acceptance suite (``tests/test_project_summary_api.py``); these tests
stay pure and fast.
"""

from __future__ import annotations

from app.persistence.models import VIDEO_PIPELINE_STATES
from app.persistence.summaries import (
    NEXT_ACTION_BLOCKERS,
    NEXT_ACTION_NONE,
    NEXT_ACTION_STATUSES,
    determine_next_action,
    map_video_status_counts,
)


def test_by_status_has_all_13_statuses_with_zeroes() -> None:
    """AC3: every approved status is present, zero-filled when absent."""
    counts = map_video_status_counts({"completed": 2, "failed": 1})
    assert list(counts.by_status.keys()) == list(VIDEO_PIPELINE_STATES)
    assert counts.by_status["completed"] == 2
    assert counts.by_status["failed"] == 1
    assert counts.by_status["imported"] == 0
    assert counts.by_status["archived"] == 0
    assert len(counts.by_status) == 13


def test_counts_active_archived_total_completed_attention() -> None:
    """AC3: active excludes archived; attention = human-decision states."""
    counts = map_video_status_counts(
        {
            "imported": 1,
            "mapping_required": 1,
            "demo_required": 1,
            "needs_review": 1,
            "failed": 1,
            "completed": 2,
            "archived": 1,
        }
    )
    assert counts.total == 8
    assert counts.active == 7
    assert counts.archived == 1
    assert counts.completed == 2
    assert counts.attention == 4  # mapping_required + demo_required + needs_review + failed


def test_empty_map_is_zero_filled() -> None:
    """AC3: an empty status map still yields exact zero counts."""
    counts = map_video_status_counts({})
    assert counts.total == 0
    assert counts.active == 0
    assert counts.archived == 0
    assert counts.completed == 0
    assert counts.attention == 0
    assert counts.by_status == {status: 0 for status in VIDEO_PIPELINE_STATES}


def test_next_action_maps_each_status_deterministically() -> None:
    """AC4: each approved status maps to its stable code + video id."""
    expected = {
        "imported": "analyze_video",
        "analyzing": "analyze_video",
        "objects_ready": "map_objects",
        "mapping_required": "map_objects",
        "demo_required": "create_demo",
        "demo_approved": "apply_reskin",
        "applying_reskin": "apply_reskin",
        "needs_review": "review_work",
        "ready_to_export": "export_video",
        "rendering": "export_video",
        "failed": "retry_failed",
        "completed": NEXT_ACTION_NONE,
        "archived": NEXT_ACTION_NONE,
    }
    for status, code in expected.items():
        action = determine_next_action(
            project_status="active",
            video_status=status,
            video_id="vid-1",
        )
        assert action[0] == code, f"{status} -> {action[0]} != {code}"
        if code == NEXT_ACTION_NONE:
            assert action[1] is None
            assert action[2] is False
            assert action[3] is None
        else:
            # AC4 capability honesty: the action points at the correct
            # Video Item but stays disabled with a stable blocker because
            # the fulfilling capability has not landed yet.
            assert action[1] == "vid-1"
            assert action[2] is False
            assert action[3] in NEXT_ACTION_BLOCKERS


def test_next_action_future_capabilities_emit_stable_blockers() -> None:
    """AC4: every semantic action emits enabled=False + a stable blocker."""
    from app.persistence.summaries import (
        FUTURE_CAPABILITY_BLOCKERS,
        NEXT_ACTION_BLOCKERS,
    )

    assert set(FUTURE_CAPABILITY_BLOCKERS) == set(NEXT_ACTION_STATUSES)
    assert set(FUTURE_CAPABILITY_BLOCKERS.values()) <= set(NEXT_ACTION_BLOCKERS)
    for status in (
        "imported",
        "analyzing",
        "objects_ready",
        "mapping_required",
        "demo_required",
        "demo_approved",
        "applying_reskin",
        "needs_review",
        "ready_to_export",
        "rendering",
        "failed",
    ):
        action = determine_next_action(
            project_status="active",
            video_status=status,
            video_id="vid-1",
        )
        code = action[0]
        assert code in FUTURE_CAPABILITY_BLOCKERS
        assert action[2] is False
        assert action[3] == FUTURE_CAPABILITY_BLOCKERS[code]


def test_next_action_archived_project_is_none() -> None:
    """AC4: an archived Project has no next action, disabled, no blocker."""
    action = determine_next_action(
        project_status="archived",
        video_status="mapping_required",
        video_id="vid-1",
    )
    assert action == (NEXT_ACTION_NONE, None, False, None)


def test_next_action_archived_only_videos_is_none() -> None:
    """AC4: a project with only archived videos has no action."""
    action = determine_next_action(
        project_status="active",
        video_status="archived",
        video_id="vid-1",
        project_has_archived_only_videos=True,
    )
    assert action == (NEXT_ACTION_NONE, None, False, None)


def test_next_action_unknown_status_is_honest_none() -> None:
    """AC4: an unknown status never fabricates an action."""
    action = determine_next_action(
        project_status="active",
        video_status="made_up",
        video_id="vid-1",
    )
    assert action == (NEXT_ACTION_NONE, None, False, None)


def test_next_action_codes_are_stable_and_bounded() -> None:
    """AC4: the code vocabulary is fixed (backend codes, no prose)."""
    from app.persistence.summaries import NEXT_ACTION_STATUSES
    from app.schemas import NextActionCode

    assert set(NEXT_ACTION_STATUSES) == {
        code.value for code in NextActionCode if code.value != NEXT_ACTION_NONE
    }
