from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from terra_scout import __version__

app = typer.Typer(help="TerraScout: evidence-driven archaeological remote-sensing research.")
datasets_app = typer.Typer(help="Search and download public elevation datasets.")
agents_app = typer.Typer(help="Run the typed research swarm.")
app.add_typer(datasets_app, name="datasets")
app.add_typer(agents_app, name="agents")
console = Console()


@app.callback()
def main_callback() -> None:
    """TerraScout CLI."""


@app.command()
def version() -> None:
    """Print the package version."""
    console.print(__version__)


@app.command()
def analyze(
    dem: Path = typer.Option(..., exists=True, readable=True, help="Path to a DEM GeoTIFF"),
    output_dir: Path = typer.Option(
        Path("output/analyze"),
        help="Directory for layers and candidates",
    ),
) -> None:
    """Run terrain visualization and conventional anomaly detection. No LLM required."""
    from terra_scout.analyze import analyze_dem

    written = analyze_dem(dem, output_dir)
    console.print(f"Wrote {len(written)} products to {output_dir}")
    for name, path in written.items():
        console.print(f"  {name}: {path}")
    console.print("Anomaly detection is not archaeological confirmation.")


@datasets_app.command("search")
def datasets_search(
    bbox: str = typer.Option(..., help="minx,miny,maxx,maxy in WGS84"),
) -> None:
    """Search USGS TNM Access and 3DEP coverage for a bounding box."""
    from terra_scout.data.usgs import search_usgs_products

    west, south, east, north = _parse_bbox(bbox)
    products = search_usgs_products(west, south, east, north)
    if not products:
        console.print("No USGS products matched this bbox. Coverage is not universal.")
        raise typer.Exit(code=0)
    for product in products:
        url = product.download_url or "no-download"
        console.print(f"{product.title}  {product.dataset}  {url}")


@datasets_app.command("download")
def datasets_download(
    bbox: str = typer.Option(..., help="minx,miny,maxx,maxy in WGS84"),
    max_megabytes: float | None = typer.Option(
        None,
        help="Refuse downloads larger than this (default: TERRASCOUT_MAX_DOWNLOAD_MEGABYTES)",
    ),
    output_dir: Path = typer.Option(Path("data/cache"), help="Cache directory"),
) -> None:
    """Download a size-capped USGS 3DEP ImageServer subset."""
    from terra_scout.config import get_settings
    from terra_scout.data.usgs import download_3dep_subset

    if max_megabytes is None:
        max_megabytes = get_settings().max_download_megabytes
    west, south, east, north = _parse_bbox(bbox)
    path = download_3dep_subset(
        west,
        south,
        east,
        north,
        output_dir=output_dir,
        max_megabytes=max_megabytes,
    )
    console.print(f"Wrote {path}")


@agents_app.command("run")
def agents_run(
    dem: Path = typer.Option(..., exists=True, readable=True),
    study_area: Path | None = typer.Option(None, help="Optional GeoJSON polygon"),
    output_dir: Path = typer.Option(Path("output/agents")),
    place_name: str | None = typer.Option(
        None,
        "--place-name",
        help="Coarse place name for literature notes. Never a coordinate substitute.",
    ),
) -> None:
    """Run geospatial, detection, research, skeptic, verification, and reporting agents."""
    from terra_scout.agents.orchestrator import run_swarm

    report = run_swarm(
        dem_path=dem,
        study_area_path=study_area,
        output_dir=output_dir,
        place_name=place_name,
    )
    console.print(report.summary)
    console.print(f"Wrote {report.report_path}")


@app.command()
def dashboard(
    host: str = typer.Option(
        "127.0.0.1",
        help="Bind address; keep loopback for unpublished coordinates",
    ),
    port: int = typer.Option(8501),
) -> None:
    """Start the localhost research dashboard."""
    import subprocess
    import sys

    app_path = Path(__file__).parent / "dashboard" / "app.py"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
    ]
    console.print(f"Starting dashboard on http://{host}:{port} (local-only by default)")
    subprocess.run(command, check=False)


@app.command()
def benchmark(
    config: Path = typer.Option(Path("experiments/synthetic.yaml"), exists=False),
    output_dir: Path = typer.Option(Path("output/benchmarks")),
) -> None:
    """Compare conventional, single-agent, and swarm detection on labeled fixtures."""
    from terra_scout.eval.benchmark import run_benchmark

    result_path = run_benchmark(config_path=config, output_dir=output_dir)
    console.print(f"Wrote {result_path}")


def _parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in bbox.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter("bbox must be minx,miny,maxx,maxy")
    west, south, east, north = (float(part) for part in parts)
    if west >= east or south >= north:
        raise typer.BadParameter("bbox must have west < east and south < north")
    return west, south, east, north
