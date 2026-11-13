from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from terra_scout.agents.schemas import AgentTrace


def write_agent_traces(
    path: Path,
    *,
    summary: str,
    llm_was_used: bool,
    candidate_count: int,
    traces: list[AgentTrace],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "llm_was_used": llm_was_used,
        "candidate_count": candidate_count,
        "traces": [trace.model_dump(mode="json") for trace in traces],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_agent_traces(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "traces" not in payload:
        return None
    return payload
