from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from terra_scout.config import get_settings
from terra_scout.coverage.index import CoverageIndex
from terra_scout.coverage.process import DEFAULT_STALE_RUNNING_SECONDS, process_batch, process_next

DEFAULT_COVERAGE_ROOT = Path("output/coverage")

coverage_app = typer.Typer(help="Progressive CONUS coverage board and tile processor.")
console = Console()


def _parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in bbox.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter("bbox must be minx,miny,maxx,maxy")
    west, south, east, north = (float(part) for part in parts)
    if west >= east or south >= north:
        raise typer.BadParameter("bbox must have west < east and south < north")
    return west, south, east, north


@coverage_app.callback()
def coverage_callback(
    ctx: typer.Context,
    root: Path = typer.Option(
        DEFAULT_COVERAGE_ROOT,
        "--root",
        help="Coverage workspace root (SQLite index, cache, studies).",
        file_okay=False,
    ),
) -> None:
    """Commands share --root (default output/coverage)."""
    ctx.obj = {"root": root}


@coverage_app.command("init")
def coverage_init(ctx: typer.Context) -> None:
    """Create the coverage SQLite index under --root."""
    root: Path = ctx.obj["root"]
    path = CoverageIndex(root).init()
    console.print(f"Initialized coverage index at {path}")


@coverage_app.command("seed-demo")
def coverage_seed_demo(
    ctx: typer.Context,
    allow_scanned: bool = typer.Option(False, help="Re-queue tiles already marked scanned."),
) -> None:
    """Enqueue demo bbox tiles (README public 3DEP box)."""
    root: Path = ctx.obj["root"]
    index = CoverageIndex(root)
    index.init()
    added = index.enqueue_demo_seed(allow_scanned=allow_scanned)
    console.print(f"Queued {added} demo tile(s) under {root}")


@coverage_app.command("enqueue")
def coverage_enqueue(
    ctx: typer.Context,
    bbox: str = typer.Option(..., help="minx,miny,maxx,maxy in WGS84"),
    allow_scanned: bool = typer.Option(False, help="Re-queue tiles already marked scanned."),
) -> None:
    """Enqueue every grid tile intersecting a bbox."""
    root: Path = ctx.obj["root"]
    west, south, east, north = _parse_bbox(bbox)
    index = CoverageIndex(root)
    index.init()
    added = index.enqueue_bbox(west, south, east, north, allow_scanned=allow_scanned)
    console.print(f"Queued {added} tile(s) for bbox {bbox}")


@coverage_app.command("process")
def coverage_process(
    ctx: typer.Context,
    next_tile: bool = typer.Option(
        False,
        "--next",
        help="Process one queued tile (default when no count).",
    ),
    count: int = typer.Option(
        0,
        "--count",
        help="Process up to N queued tiles in one batch.",
    ),
    max_megabytes: float | None = typer.Option(
        None,
        help="Per-tile download cap (default TERRASCOUT_MAX_DOWNLOAD_MEGABYTES).",
    ),
    stale_seconds: float = typer.Option(
        DEFAULT_STALE_RUNNING_SECONDS,
        help="Reset running tiles older than this many seconds.",
    ),
) -> None:
    """Download, analyze, and mark the next queued tile(s)."""
    root: Path = ctx.obj["root"]
    cap = max_megabytes if max_megabytes is not None else get_settings().max_download_megabytes
    if count > 0:
        outcomes = process_batch(
            root,
            count=count,
            max_megabytes=cap,
            stale_seconds=stale_seconds,
        )
        if not outcomes:
            console.print("No queued tiles.")
            raise typer.Exit(code=0)
        for outcome in outcomes:
            console.print(
                f"{outcome.tile_id}: {outcome.status}"
                + (f" -> {outcome.study_dir}" if outcome.study_dir else "")
                + (f" ({outcome.message})" if outcome.message else "")
            )
        return
    if not next_tile:
        raise typer.BadParameter("Pass --next or --count N to process tiles.")
    outcome = process_next(root, max_megabytes=cap, stale_seconds=stale_seconds)
    if outcome is None:
        console.print("No queued tiles.")
        raise typer.Exit(code=0)
    console.print(
        f"{outcome.tile_id}: {outcome.status}"
        + (f" -> {outcome.study_dir}" if outcome.study_dir else "")
        + (f" ({outcome.message})" if outcome.message else "")
    )


@coverage_app.command("status")
def coverage_status(ctx: typer.Context) -> None:
    """Show virtual unscanned counts and recent tile rows."""
    root: Path = ctx.obj["root"]
    index = CoverageIndex(root)
    if not index.db_path.exists():
        console.print(f"No index at {index.db_path}; run coverage init first.")
        raise typer.Exit(code=1)
    counts = index.status_counts()
    table = Table(title=f"CONUS coverage ({root})")
    table.add_column("status")
    table.add_column("count", justify="right")
    for key in ("unscanned", "queued", "running", "scanned", "skipped", "failed"):
        table.add_row(key, str(counts.get(key, 0)))
    console.print(table)
    recent = index.list_tiles(limit=20)
    if recent:
        console.print("Recent tiles:")
        for tile in recent:
            study = tile.study_dir or "—"
            console.print(f"  {tile.tile_id}  {tile.status}  {study}")