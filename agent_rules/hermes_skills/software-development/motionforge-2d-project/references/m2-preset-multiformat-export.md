# M2: Preset Manager, Multi-Format Render, Export ZIP

## New service: `app/workflow/preset_service.py`
- `CharacterMapping` — single character-to-asset mapping (original_name, replacement_asset, voice_config, replacement_config)
- `ProjectPreset` — reusable preset (name, description, version, mappings, dubbing_config)
- `PresetService` — save/load/list/apply presets
  - `save_preset(preset, output_path)` → writes JSON via `model_dump_json(indent=2)`
  - `load_preset(path)` → reads JSON, validates via `ProjectPreset.model_validate()`
  - `list_presets(dir)` → globs `*.json`, returns metadata dicts
  - `apply_preset_to_project(preset, project_data)` → matches objects by `name == mapping.original_name`, updates `replacement_config` fields via `setattr`

## New endpoints in `app/api/routes/projects.py`

### Scene objects
- `GET /{project_id}/scenes/{scene_id}/objects` — filters `proj.objects` by `scene_id`, returns `model_dump(by_alias=True)`

### Presets
- `POST /{project_id}/presets/save` — builds `CharacterMapping` list from project objects, saves to `presets/` dir
- `GET /{project_id}/presets` — lists presets via `PresetService.list_presets()`
- `POST /{project_id}/presets/{preset_filename}/apply` — loads preset, applies to project, saves

### Multi-format render
- `POST /{project_id}/render` now accepts `format: str = "mp4"` query param
- Helper `get_format_params(fmt)` in `render_service.py` returns `{ext, codec, pix_fmt}` for mp4/webm/gif

### Export ZIP
- `GET /{project_id}/export` — creates ZIP with:
  - `renders/*.mp4`, `renders/*.webm`
  - `dubbing/**/*.srt`, `dubbing/**/*.wav`
  - `project.json`
  - `presets/*.json`
- Returns `FileResponse` with `media_type="application/zip"`

## Pitfalls
- When building `CharacterMapping` from project objects, handle `replacement_config=None` case (objects without replacement config yet)
- Preset filename is derived from name: `body.name.lower().replace(' ', '_') + ".json"`
- `apply_preset_to_project` uses `setattr` on `replacement_config` — only works for fields that exist on the model; silently skips unknown keys
