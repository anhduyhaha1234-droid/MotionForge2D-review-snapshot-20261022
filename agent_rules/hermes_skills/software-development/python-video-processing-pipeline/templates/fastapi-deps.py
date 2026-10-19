"""FastAPI dependency injection — singleton services.

Pattern: module-level singletons with getter functions.
Testable via monkeypatch.setattr on the module attributes.
"""

from __future__ import annotations

from app.config import AppConfig, config
# Import all workflow services here

# Singletons — initialized once at import time
_config: AppConfig = config
# _job_service = JobService()
# _project_wf = ProjectWorkflowService(_config)
# ...

# Getter functions — endpoints call these
def get_config() -> AppConfig:
    return _config

# def get_job_service() -> JobService:
#     return _job_service
# ...

# --- Test override pattern (in conftest.py) ---
# @pytest.fixture(autouse=True)
# def _patch_deps(tmp_path, monkeypatch):
#     from app.api import deps
#     test_config = AppConfig(project_root=tmp_path / "test", ...)
#     monkeypatch.setattr(deps, "_config", test_config)
#     monkeypatch.setattr(deps, "_job_service", JobService())
#     # ... etc
