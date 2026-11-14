from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from terra_scout.coverage.index import CoverageIndex
from terra_scout.dashboard.acquire import acquire_and_analyze
from terra_scout.dashboard.manifest import write_run_manifest
from terra_scout.data.usgs import DownloadLimitExceeded
from terra_scout.io.dem import DemValidationError

_SKIP_MARKERS = (
    "no coverage",
    "no data",
    "nodata",
    "no finite elevation",
    "json instead of geotiff",
    "instead of geotiff",
)


@dataclass(frozen=True)
class ProcessResult:
    tile_id: str
    status: str
    study_dir: Path | None
    message: str | None


def _pin_dem(
    study_dir: Path,
    *,
    dem_path: Path,
    observation_kind: str,
) -> Path:
    study_dir.mkdir(parents=True, exist_ok=True)
    dest = study_dir / dem_path.name
    shutil.copy2(dem_path, dest)
    write_run_manifest(
        study_dir,
        dem_path=dest,
        observation_kind=observation_kind,
    )
    return dest


def _prepare_study_dir(study_dir: Path) -> None:
    if study_dir.exists():
        shutil.rmtree(study_dir)
    study_dir.mkdir(parents=True, exist_ok=True)


def _failure_status(error: BaseException) -> str:
    if isinstance(error, DemValidationError) or type(error).__name__ == "DemValidationError":
        return "skipped"
    message = str(error).lower()
    if any(marker in message for marker in _SKIP_MARKERS):
        return "skipped"
    return "failed"


def process_next(
    index: CoverageIndex,
    *,
    n: int,
    cache_dir: Path,
    max_megabytes: float,
    tiles_root: Path,
) -> list[ProcessResult]:
    if n <= 0:
        return []
    index.reset_stale_running()
    tiles = index.dequeue_queued(n)
    if not tiles:
        return []

    cache_dir.mkdir(parents=True, exist_ok=True)
    outcomes: list[ProcessResult] = []

    for tile in tiles:
        study_dir = tiles_root / "tiles" / tile.tile_id
        _prepare_study_dir(study_dir)
        try:
            result = acquire_and_analyze(
                west=tile.west,
                south=tile.south,
                east=tile.east,
                north=tile.north,
                cache_dir=cache_dir,
                output_dir=study_dir,
                max_megabytes=max_megabytes,
            )
        except DownloadLimitExceeded as error:
            index.mark_status(tile.tile_id, "skipped", message=str(error))
            outcomes.append(
                ProcessResult(
                    tile_id=tile.tile_id,
                    status="skipped",
                    study_dir=None,
                    message=str(error),
                )
            )
            continue
        except (OSError, RuntimeError, ValueError) as error:
            status = _failure_status(error)
            index.mark_status(tile.tile_id, status, message=str(error))
            outcomes.append(
                ProcessResult(
                    tile_id=tile.tile_id,
                    status=status,
                    study_dir=None,
                    message=str(error),
                )
            )
            continue
        except Exception as error:
            index.mark_status(tile.tile_id, "failed", message=str(error))
            outcomes.append(
                ProcessResult(
                    tile_id=tile.tile_id,
                    status="failed",
                    study_dir=None,
                    message=str(error),
                )
            )
            continue

        _pin_dem(
            study_dir,
            dem_path=result.dem_path,
            observation_kind=result.observation_kind,
        )
        index.mark_status(
            tile.tile_id,
            "scanned",
            study_dir=study_dir,
            message=f"candidates={result.candidate_count}",
        )
        outcomes.append(
            ProcessResult(
                tile_id=tile.tile_id,
                status="scanned",
                study_dir=study_dir,
                message=f"candidates={result.candidate_count}",
            )
        )
    return outcomes