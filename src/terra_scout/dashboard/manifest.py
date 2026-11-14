from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_run_manifest(
    run_root: Path,
    *,
    dem_path: Path,
    observation_kind: str,
) -> Path:
    run_root.mkdir(parents=True, exist_ok=True)
    path = run_root / "run_manifest.json"
    payload = {
        "dem_path": str(Path(dem_path).resolve()),
        "observation_kind": observation_kind,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_run_manifest(run_root: Path) -> dict[str, Any] | None:
    path = run_root / "run_manifest.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "dem_path" not in payload:
        return None
    return payload


def resolve_dem_path(run_root: Path, sidebar_override: str | None) -> Path | None:
    if sidebar_override is not None and str(sidebar_override).strip():
        candidate = Path(str(sidebar_override).strip()).expanduser()
        return candidate.resolve() if candidate.is_file() else None
    manifest = load_run_manifest(run_root)
    if manifest is None:
        return None
    candidate = Path(str(manifest["dem_path"]))
    return candidate.resolve() if candidate.is_file() else None
