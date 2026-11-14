from __future__ import annotations

import json
from pathlib import Path
from typing import Any

KNOWN_AGENT_IDS = [
    "geospatial",
    "detection",
    "research",
    "skeptic",
    "verification",
    "reporting",
]


def load_agent_traces(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "traces" not in payload:
        return None
    return payload


def _notes_preview(notes: Any) -> str | None:
    if not notes:
        return None
    if isinstance(notes, list):
        text = "; ".join(str(item) for item in notes if str(item).strip())
    else:
        text = str(notes)
    text = text.strip()
    if not text:
        return None
    if len(text) > 120:
        return text[:117] + "..."
    return text


def agent_status_rows(
    traces_payload: dict[str, Any] | None,
    run_state: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Honest per-agent rows: pending while running without traces; done from traces."""
    by_id: dict[str, dict[str, Any]] = {}
    if traces_payload is not None:
        raw_traces = traces_payload.get("traces") or []
        if isinstance(raw_traces, list):
            for item in raw_traces:
                if not isinstance(item, dict):
                    continue
                agent_id = str(item.get("agent_id") or "").strip()
                if not agent_id:
                    continue
                by_id[agent_id] = {
                    "agent_id": agent_id,
                    "status": "done",
                    "timestamp": item.get("timestamp"),
                    "notes_preview": _notes_preview(item.get("notes")),
                }

    status = (run_state or {}).get("status")
    rows: list[dict[str, Any]] = []
    for index, agent_id in enumerate(KNOWN_AGENT_IDS):
        if agent_id in by_id:
            rows.append(by_id[agent_id])
            continue
        if status == "running" and not by_id:
            # Orchestrator writes traces at end — do not fake mid-agent %.
            row_status = "running" if index == 0 else "pending"
            rows.append(
                {
                    "agent_id": agent_id,
                    "status": row_status,
                    "timestamp": None,
                    "notes_preview": None,
                }
            )
        elif status == "running":
            rows.append(
                {
                    "agent_id": agent_id,
                    "status": "pending",
                    "timestamp": None,
                    "notes_preview": None,
                }
            )
        else:
            rows.append(
                {
                    "agent_id": agent_id,
                    "status": "unknown" if by_id else "pending",
                    "timestamp": None,
                    "notes_preview": None,
                }
            )
    return rows
