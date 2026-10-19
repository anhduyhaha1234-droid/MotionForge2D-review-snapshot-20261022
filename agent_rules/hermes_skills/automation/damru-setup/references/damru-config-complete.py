"""Damru configuration — known-good complete template.

This file contains ALL variables imported by damru/docker.py and damru/cli.py.
Both shipped templates (config.py.windows, config.py.linux) are MISSING variables.
Use this as the authoritative reference when creating or repairing config.py.

CRITICAL: If docker.py or cli.py throws ImportError on a config variable,
check this file first. The missing variable was likely omitted from the
shipped templates.
"""

import os

# ── Pool Defaults ──────────────────────────────────────────────────────
MODE = "auto"                     # "auto" = Docker/Redroid, "mumu" = MuMu, "manual" = existing ADB
NUM_DEVICES = 1                   # Concurrent browser instances (= containers)
DEVICE = None                     # Fixed device name or None for random per session
PROFILE_TIER = os.environ.get("DAMRU_PROFILE_TIER", "premium")

# ── Proxy ──────────────────────────────────────────────────────────────
PROXY = None                      # SOCKS5: "socks5://user:pass@host:port"
HTTP_PROXY = None                 # HTTP for Android system: "host:port"
PROXIES = None                    # Per-worker list: ["socks5://h1:p", "socks5://h2:p"]
HTTP_PROXIES = None               # Per-worker HTTP list

# ── Location (auto from proxy if None) ────────────────────────────────
TIMEZONE = None                   # IANA timezone, e.g. "Asia/Ho_Chi_Minh"
LOCALE = None                     # BCP-47 locale, e.g. "vi-VN"

# ── Chrome APK ────────────────────────────────────────────────────────
CHROME_APK = None                 # None = auto-search chrome-apks/

# ── WSL2 (required even on native Linux — must be present) ────────────
WSL_DISTRO = "Ubuntu"
WSL_USERNAME = "root"             # Set to your WSL username
WSL_PASSWORD = ""                 # Compatibility only; wsl -u root used instead

# ── MuMu (Windows-only, not supported) ────────────────────────────────
MUMU_MANAGER_PATH = None
MUMU_INSTANCE_INDICES = None
MUMU_AUTO_CREATE = False
MUMU_CPU = 2
MUMU_MEMORY_GB = 1
MUMU_STRICT_RESOURCE_LIMIT = True
MUMU_BOOT_FALLBACK_CPU = 2
MUMU_BOOT_FALLBACK_MEMORY_GB = 2
MUMU_SYSTEM_DISK_WRITABLE = True

# ── Redroid Container Settings ────────────────────────────────────────
REDROID_IMAGE = "damru-redroid:latest"
REDROID_BASE_IMAGE = "redroid/redroid:14.0.0_64only-latest"  # MISSING from both shipped templates; actual value from docker.py
REDROID_BASE_PORT = 5600
REDROID_CONTAINER_PREFIX = "damru-worker-"
REDROID_CPUS = 2.0
REDROID_MEMORY = "2g"
REDROID_GPU_MODE = "guest"        # "host" for GPU passthrough
REDROID_SETUPWIZARD_DISABLED = True

# ── Timeouts ──────────────────────────────────────────────────────────
CONTAINER_BOOT_TIMEOUT = 90
DOCKER_CMD_TIMEOUT = 30
APK_INSTALL_TIMEOUT = 120
SESSION_SETUP_TIMEOUT = 120
MAX_SESSION_RETRIES = 2
HEALTH_CHECK_INTERVAL = 30
MAX_SLOT_FAILURES = 3
DEBUG = False
