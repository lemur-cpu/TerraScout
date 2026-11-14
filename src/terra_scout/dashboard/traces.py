from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_agent_traces(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "traces" not in payload:
        return None
    return payload
