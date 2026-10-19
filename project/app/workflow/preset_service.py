"""Project preset manager — save/load character mapping presets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class CharacterMapping(BaseModel):
    """A single character-to-asset mapping."""

    original_name: str = ""
    replacement_asset: str = ""
    voice_config: dict[str, Any] = Field(default_factory=dict)
    replacement_config: dict[str, Any] = Field(default_factory=dict)


class ProjectPreset(BaseModel):
    """A reusable preset for character replacement configurations."""

    name: str = "Untitled Preset"
    description: str = ""
    version: str = "1.0.0"
    mappings: list[CharacterMapping] = Field(default_factory=list)
    dubbing_config: dict[str, Any] = Field(default_factory=dict)


class PresetService:
    """Save and load project presets."""

    def save_preset(
        self,
        preset: ProjectPreset,
        output_path: Path,
    ) -> Path:
        """Save preset to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            preset.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return output_path

    def load_preset(self, preset_path: Path) -> ProjectPreset:
        """Load preset from JSON file."""
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {preset_path}")
        data = json.loads(preset_path.read_text(encoding="utf-8"))
        return ProjectPreset.model_validate(data)

    def list_presets(self, presets_dir: Path) -> list[dict[str, Any]]:
        """List all presets in a directory."""
        if not presets_dir.exists():
            return []
        presets: list[dict[str, Any]] = []
        for p in sorted(presets_dir.glob("*.json")):
            try:
                preset = self.load_preset(p)
                presets.append({
                    "filename": p.name,
                    "name": preset.name,
                    "description": preset.description,
                    "mapping_count": len(preset.mappings),
                })
            except Exception:
                continue
        return presets

    def apply_preset_to_project(
        self,
        preset: ProjectPreset,
        project_data: Any,
    ) -> int:
        """Apply preset mappings to matching objects in a project.

        Matches by original_name field.

        Returns:
            Number of objects updated.
        """
        updated = 0
        for mapping in preset.mappings:
            for obj in project_data.objects:
                if obj.name == mapping.original_name:
                    if mapping.replacement_config:
                        for k, v in mapping.replacement_config.items():
                            if hasattr(obj.replacement_config, k):
                                setattr(obj.replacement_config, k, v)
                    updated += 1
        return updated
