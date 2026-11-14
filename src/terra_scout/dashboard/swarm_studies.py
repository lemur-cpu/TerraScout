from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terra_scout.dashboard.manifest import load_run_manifest


@dataclass(frozen=True)
class SwarmStudy:
    label: str
    tile_id: str | None
    output_dir: Path
    dem_path: Path


def _find_dem_in_dir(study_dir: Path) -> Path | None:
    manifest = load_run_manifest(study_dir)
    if manifest is not None:
        candidate = Path(str(manifest["dem_path"]))
        if candidate.is_file():
            return candidate.resolve()
    tifs = sorted(study_dir.glob("*.tif")) + sorted(study_dir.glob("*.tiff"))
    for path in tifs:
        if path.is_file():
            return path.resolve()
    return None


def resolve_study(output_dir: Path) -> SwarmStudy | None:
    study_dir = Path(output_dir)
    if not study_dir.is_dir():
        return None
    dem = _find_dem_in_dir(study_dir)
    if dem is None:
        return None
    name = study_dir.name
    return SwarmStudy(
        label=name,
        tile_id=name if (study_dir.parent.name == "tiles") else None,
        output_dir=study_dir.resolve(),
        dem_path=dem,
    )


def list_runnable_studies(coverage_root: Path) -> list[SwarmStudy]:
    tiles_root = Path(coverage_root) / "tiles"
    if not tiles_root.is_dir():
        return []
    studies: list[SwarmStudy] = []
    for tile_dir in sorted(p for p in tiles_root.iterdir() if p.is_dir()):
        dem = _find_dem_in_dir(tile_dir)
        if dem is None:
            continue
        studies.append(
            SwarmStudy(
                label=tile_dir.name,
                tile_id=tile_dir.name,
                output_dir=tile_dir.resolve(),
                dem_path=dem,
            )
        )
    return studies
