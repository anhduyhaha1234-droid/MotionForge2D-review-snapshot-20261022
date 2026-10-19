#!/usr/bin/env python
"""OpenAPI parameter-leak probe — verify NO client-controlled parameter leaks.

Class of finding it proves/disproves (worker-orchestration pitfall 40):
any FastAPI handler parameter WITH A DEFAULT VALUE silently becomes a
client-controlled query parameter. Codex-style P1 "client can choose
workspace/tenant via query param" is verified deterministically by scanning
/openapi.json instead of reading every handler.

Usage (run from the repo root whose FastAPI app you are auditing):

    python openapi_param_leak_probe.py <app-import-string> \
        [--path-substr project-cast] [--forbid workspace_id] [...more names]

    <app-import-string>   e.g. app.api.app:app  (module:attr)
    --path-substr         only audit operations whose path contains this
                          (repeatable; omit = audit all paths)
    --forbid              parameter name(s) that must NOT appear as an
                          operation parameter (repeatable; default: workspace_id)

Exit codes: 0 = no leaks; 1 = leaks found (printed); 2 = import/app error.
Prints every leaking operation as `METHOD PATH -> param (in=...)` so output
can be tee'd directly into correction evidence dirs.

Verified pattern (S07-T01-C4, 2026-08-22): pre-fix probe listed 20 leaking
project-cast operations; post-fix same probe printing nothing IS the
acceptance evidence. Requires MOTIONFORGE_DATABASE_URL (or equivalent prod
DB env) to be UNSET before importing the app.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_import", help="FastAPI app as module:attr")
    parser.add_argument(
        "--path-substr",
        action="append",
        default=[],
        help="only audit paths containing this substring (repeatable)",
    )
    parser.add_argument(
        "--forbid",
        action="append",
        default=["workspace_id"],
        help="forbidden parameter names (repeatable)",
    )
    args = parser.parse_args()

    try:
        module_name, _, attr_name = args.app_import.partition(":")
        import importlib

        module = importlib.import_module(module_name)
        app = getattr(module, attr_name) if attr_name else module.app
    except Exception as exc:  # noqa: BLE001 - report any import failure cleanly
        print(f"APP_IMPORT_ERROR: {exc}", file=sys.stderr)
        return 2

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()
    if not isinstance(spec, dict) or "paths" not in spec:
        print("OPENAPI_FETCH_ERROR: /openapi.json returned no paths", file=sys.stderr)
        return 2

    forbidden = set(args.forbid)
    leaks: list[str] = []
    audited_ops = 0
    for path, operations in spec["paths"].items():
        if args.path_substr and not any(s in path for s in args.path_substr):
            continue
        for method, operation in operations.items():
            if not isinstance(operation, dict):
                continue
            audited_ops += 1
            for parameter in operation.get("parameters", []):
                name = parameter.get("name", "")
                if name in forbidden:
                    leaks.append(
                        f"{method.upper()} {path} -> {name} (in={parameter.get('in')})"
                    )

    print(f"audited_operations={audited_ops} forbidden={sorted(forbidden)}")
    if leaks:
        print("LEAKS:")
        for leak in leaks:
            print(" ", leak)
        return 1
    print("OK: no forbidden parameters exposed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
