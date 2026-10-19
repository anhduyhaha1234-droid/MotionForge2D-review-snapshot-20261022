# Start Prompt — Task S06-T03: Pose Validation Engine

## Context
Implement S06-T03 character pack pose validation engine in `app/workflow/character_validator.py`.

## Requirements
- Validate all 6 core pose slots (`front`, `three_quarter`, `side`, `back`, `sitting`, `walking`).
- Check image dimensions (minimum width/height), alpha channel transparency, and file integrity.
- Prevent version publishing if any core slot is missing or invalid.
