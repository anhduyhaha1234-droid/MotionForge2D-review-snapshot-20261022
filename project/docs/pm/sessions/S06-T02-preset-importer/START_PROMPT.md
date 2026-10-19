# Start Prompt — Task S06-T02: Preset Character Asset Importer

## Context
Implement S06-T02 preset importer in `app/workflow/character_preset_importer.py`. Copy preset files to managed storage, register artifacts, create draft character, and attach pose assets.

## Requirements
- Never mutate original preset files.
- Calculate SHA256 checksum and file size for every copied asset.
- Register `Artifact` in state `ready`.
- Create draft `Character` and `CharacterPackVersion`.
- Attach assets to `pose_slot`s.
