from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from terra_scout.coverage.grid import demo_seed_tiles, parse_tile_id
from terra_scout.coverage.index import CoverageIndex
from terra_scout.coverage.process import _pin_dem, process_next
from terra_scout.dashboard.acquire import AcquireResult
from terra_scout.data.usgs import DownloadLimitExceeded
from terra_scout.io.dem import DemValidationError


def _db(root: Path) -> CoverageIndex:
    index = CoverageIndex(root / "coverage.sqlite3")
    index.ensure_open()
    return index


def test_process_next_scanned_and_pins_dem(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    first_tid = demo_seed_tiles()[0]
    ix, iy = parse_tile_id(first_tid)
    index.enqueue(ix, iy)
    study_dir = root / "tiles" / first_tid
    dem_path = root / "cache" / "tile.tif"

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.return_value = AcquireResult(
            dem_path=dem_path,
            output_dir=study_dir,
            observation_kind="usgs_3dep",
            candidate_count=3,
        )
        dem_path.parent.mkdir(parents=True)
        dem_path.write_bytes(b"dem")
        outcomes = process_next(
            index,
            n=1,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert len(outcomes) == 1
    assert outcomes[0].status == "scanned"
    assert outcomes[0].study_dir == study_dir
    assert (study_dir / dem_path.name).is_file()
    assert (study_dir / "run_manifest.json").is_file()
    assert index.status_counts()["scanned"] == 1


def test_pin_dem_copies_and_writes_manifest(tmp_path: Path) -> None:
    dem = tmp_path / "src.tif"
    dem.write_bytes(b"x")
    study = tmp_path / "study"
    dest = _pin_dem(study, dem_path=dem, observation_kind="synthetic")
    assert dest.is_file()
    assert (study / "run_manifest.json").exists()


def test_process_next_skips_on_download_limit(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    seeds = demo_seed_tiles()[:2]
    for tid in seeds:
        ix, iy = parse_tile_id(tid)
        index.enqueue(ix, iy)

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = DownloadLimitExceeded("too big")
        outcomes = process_next(
            index,
            n=2,
            cache_dir=root / "cache",
            max_megabytes=1.0,
            tiles_root=root,
        )

    assert len(outcomes) == 2
    assert all(item.status == "skipped" for item in outcomes)
    assert index.status_counts()["skipped"] == 2


def test_process_no_coverage_message_skipped(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    ix, iy = parse_tile_id(demo_seed_tiles()[0])
    index.enqueue(ix, iy)

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = RuntimeError("no coverage in bbox")
        outcomes = process_next(
            index,
            n=1,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert outcomes[0].status == "skipped"


def test_process_batch_continues_after_failure(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    seeds = demo_seed_tiles()[:2]
    for tid in seeds:
        ix, iy = parse_tile_id(tid)
        index.enqueue(ix, iy)
    study_dir = root / "tiles" / seeds[1]

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = [
            ValueError("hard fail"),
            AcquireResult(
                dem_path=root / "cache" / "b.tif",
                output_dir=study_dir,
                observation_kind="synthetic",
                candidate_count=0,
            ),
        ]
        (root / "cache" / "b.tif").parent.mkdir(parents=True)
        (root / "cache" / "b.tif").write_bytes(b"d")
        outcomes = process_next(
            index,
            n=2,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert len(outcomes) == 2
    assert outcomes[0].status == "failed"
    assert outcomes[1].status == "scanned"


def test_rescan_clears_prior_study_folder(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    first_tid = demo_seed_tiles()[0]
    ix, iy = parse_tile_id(first_tid)
    index.enqueue(ix, iy)
    study_dir = root / "tiles" / first_tid
    study_dir.mkdir(parents=True)
    stale = study_dir / "stale.txt"
    stale.write_text("old run", encoding="utf-8")
    dem_path = root / "cache" / "tile.tif"
    dem_path.parent.mkdir(parents=True)
    dem_path.write_bytes(b"dem")

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.return_value = AcquireResult(
            dem_path=dem_path,
            output_dir=study_dir,
            observation_kind="usgs_3dep",
            candidate_count=1,
        )
        process_next(
            index,
            n=1,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert not stale.exists()
    assert (study_dir / dem_path.name).is_file()


def test_dem_validation_and_json_export_are_skipped(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    seeds = demo_seed_tiles()[:2]
    for tid in seeds:
        ix, iy = parse_tile_id(tid)
        index.enqueue(ix, iy)

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = [
            DemValidationError("DEM contains no finite elevation samples"),
            RuntimeError("server returned json instead of geotiff"),
        ]
        outcomes = process_next(
            index,
            n=2,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert len(outcomes) == 2
    assert all(item.status == "skipped" for item in outcomes)
    assert index.status_counts()["skipped"] == 2


def test_keyerror_marks_failed_and_continues(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    seeds = demo_seed_tiles()[:2]
    for tid in seeds:
        ix, iy = parse_tile_id(tid)
        index.enqueue(ix, iy)
    study_dir = root / "tiles" / seeds[1]
    dem_path = root / "cache" / "b.tif"
    dem_path.parent.mkdir(parents=True)
    dem_path.write_bytes(b"d")

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = [
            KeyError("missing_layer"),
            AcquireResult(
                dem_path=dem_path,
                output_dir=study_dir,
                observation_kind="synthetic",
                candidate_count=0,
            ),
        ]
        outcomes = process_next(
            index,
            n=2,
            cache_dir=root / "cache",
            max_megabytes=5.0,
            tiles_root=root,
        )

    assert len(outcomes) == 2
    assert outcomes[0].status == "failed"
    assert outcomes[1].status == "scanned"


def test_process_next_stops_when_queue_empty(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = _db(root)
    outcomes = process_next(
        index,
        n=3,
        cache_dir=root / "cache",
        max_megabytes=5.0,
        tiles_root=root,
    )
    assert outcomes == []