# Task S06-T05: Pack Review, Publish & Immutable Version UX

- **Task ID:** `S06-T05`
- **Sprint:** `S06` (Durable Character Library)
- **Status:** `IMPLEMENTATION`
- **Owner:** Hermes (Parallel Worktree `s06-t01`)
- **Depends On:** `S06-T04`

## Objectives
1. Implement Character Pack Review & Publish UX in `frontend/src/app/(app)/characters/page.tsx` and endpoints `/api/v2/characters/{id}/versions/{v}/publish`.
2. Features:
   - Preview of 6 core pose slots (`front`, `three_quarter`, `side`, `back`, `sitting`, `walking`).
   - Pose completeness validation indicator banner (shows green "Publish Ready" or amber "Missing 2 pose slots").
   - "Publish Pack Version v1" action button with confirmation dialog and CAS revision handling.
   - Immutable published version badge preventing further asset mutations.
