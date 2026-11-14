from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terra_scout.coverage.index import CoverageIndex
from terra_scout.dashboard.acquire import acquire_and_analyze
from terra_scout.data.usgs import DownloadLimitExceeded


@dataclass(frozen=True)
class ProcessOutcome:
    tile_id: str
    status: str
    study_dir: Path | None
    message: str | None


DEFAULT_STALE_RUNNING_SECONDS = 3600.0


def process_next(
    root: Path,
    *,
    max_megabytes: float,
    stale_seconds: float = DEFAULT_STALE_RUNNING_SECONDS,
) -> ProcessOutcome | None:
    index = CoverageIndex(root)
    index.init()
    index.reset_stale_running(stale_seconds)
    tile = index.dequeue_queued()
    if tile is None:
        return None

    cache_dir = root / "cache"
    study_dir = root / "studies" / tile.tile_id
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
        return ProcessOutcome(
            tile_id=tile.tile_id,
            status="skipped",
            study_dir=None,
            message=str(error),
        )
    except Exception as error:
        index.mark_status(tile.tile_id, "failed", message=str(error))
        return ProcessOutcome(
            tile_id=tile.tile_id,
            status="failed",
            study_dir=None,
            message=str(error),
        )

    index.mark_status(
        tile.tile_id,
        "scanned",
        study_dir=result.output_dir,
        message=f"candidates={result.candidate_count}",
    )
    return ProcessOutcome(
        tile_id=tile.tile_id,
        status="scanned",
        study_dir=result.output_dir,
        message=f"candidates={result.candidate_count}",
    )


def process_batch(
    root: Path,
    *,
    count: int,
    max_megabytes: float,
    stale_seconds: float = DEFAULT_STALE_RUNNING_SECONDS,
) -> list[ProcessOutcome]:
    if count <= 0:
        return []
    outcomes: list[ProcessOutcome] = []
    for _ in range(count):
        outcome = process_next(
            root,
            max_megabytes=max_megabytes,
            stale_seconds=stale_seconds,
        )
        if outcome is None:
            break
        outcomes.append(outcome)
    return outcomes