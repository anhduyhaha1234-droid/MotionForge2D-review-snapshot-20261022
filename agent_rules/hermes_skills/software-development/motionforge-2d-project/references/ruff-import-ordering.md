# Ruff Import Ordering Rules (I001, E402)

## `from __future__` import MUST have blank line after it

```python
# WRONG — ruff flags I001 + E402
from __future__ import annotations
from collections.abc import Callable
from pathlib import Path

import cv2

# CORRECT
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import cv2
```

## Import order (isort-compatible)
1. `from __future__` (always first, with blank line after)
2. stdlib (`os`, `sys`, `pathlib`, `collections.abc`, `typing`, `json`, `math`)
3. Third-party (`cv2`, `numpy`, `fastapi`, `pydantic`)
4. Local (`app.schemas`, `app.services`)

## Inside function bodies
Same stdlib-before-third-party rule applies even for local imports:
```python
def test_foo(self, tmp_path: object) -> None:
    from pathlib import Path  # stdlib first

    import cv2  # third-party second
```

## Common ruff codes
- **I001**: Import block unsorted/unformatted
- **E402**: Module-level import not at top of file (triggered when `from __future__` lacks blank line)
- **SIM108**: Use ternary instead of if/else block (not auto-fixable)
- **SIM222**: `x or True` is always true
