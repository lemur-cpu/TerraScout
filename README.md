# TerraScout

Evidence-driven research software for finding *potential* anthropogenic landscape features in public LiDAR and digital elevation models.

Anomaly detection is **not** archaeological confirmation. High `anomaly_score` values are residual/shape statistics, not calibrated probabilities that a feature is archaeological. The localhost dashboard is a **candidate site finder**: it ranks geometric anomalies and attaches an evidence packet. Novelty stays `not_demonstrated` until literature is actually retrieved. A human (and, where required, an authority) confirms. Software does not.

## Quick start

Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/lemur-cpu/TerraScout.git terra-scout
cd terra-scout
uv sync --extra dev
uv run ruff check src tests
uv run pytest
```

Analyze a local DEM. No API key:

```bash
uv run terra-scout analyze --dem path/to/dem.tif --output-dir output/demo
```

Expected files in `output/demo/`:

| File | What it is |
|---|---|
| `layers/hillshade.tif` | Multidirectional hillshade |
| `layers/slope_degrees.tif` | Horn 1981 slope |
| `layers/local_relief.tif` | Circular-mean local relief residual |
| `layers/curvature.tif` | Plan curvature |
| `layers/tpi.tif` | Topographic position |
| `layers/sky_view_factor.tif` | Sky-view factor |
| `layers/ruggedness.tif` | Terrain ruggedness |
| `candidates.geojson` | Anomaly polygons with scores and disclaimers |
| `preview_hillshade.png` | Quick-look image |
| `map.html` | Local Folium map |
| `report.txt` | Candidate list |
| `registry.sqlite3` | Local review registry |

On the synthetic 64×64 mound fixture used by tests, `analyze` writes a `mound_like` candidate whose score definition contains `not a calibrated archaeological probability`.

## Implemented CLI

```text
terra-scout analyze --dem FILE --output-dir DIR
terra-scout datasets search --bbox minx,miny,maxx,maxy
terra-scout datasets download --bbox minx,miny,maxx,maxy --max-megabytes 20 --output-dir data/cache
terra-scout agents run --dem FILE --study-area FILE --output-dir DIR
terra-scout dashboard --host 127.0.0.1 --port 8501
terra-scout benchmark --config experiments/synthetic.yaml --output-dir output/benchmarks
terra-scout version
```

`datasets search` queries USGS TNM Access. Empty results mean no matching product, not an API bug. `datasets download` pulls a size-capped 3DEP ImageServer GeoTIFF and refuses payloads over `--max-megabytes`.

## Live public DEM demonstration

This was run against USGS 3DEP ImageServer (not a mock):

- Request: 400×300 float32 GeoTIFF, bbox `-90.070,38.655,-90.055,38.665` (WGS84)
- File size: 788,288 bytes
- `observation_kind=usgs_3dep`, valid fraction 1.0
- Elevation range about 122–158 m
- Conventional detector emitted 72 **unreviewed** candidates

Those candidates are terrain anomalies on a well-documented public landscape. They are **not** new archaeological sites. Precise geometries were kept in a local `output/` tree and are gitignored.

Reproduce:

```bash
uv run terra-scout datasets download \
  --bbox "-90.070,38.655,-90.055,38.665" \
  --max-megabytes 5 \
  --output-dir data/cache
uv run terra-scout analyze --dem data/cache/usgs_3dep_m90p0700_38p6550_m90p0550_38p6650.tif \
  --output-dir output/demo
```

## Optional extras

| Extra | Command | When |
|---|---|---|
| Dev | `uv sync --extra dev` | pytest + ruff |
| LiDAR | `uv sync --extra lidar` plus system PDAL | EPT/LAS → DTM |
| ML | `uv sync --extra ml` | future PyTorch models; none are trained here |

OpenTopography and NASA Earthdata downloads need operator credentials in `.env` (see `.env.example`). They are not required for DEM analysis.

Ollama / external LLMs are optional. Geospatial, detection, and skeptic tools run without them. Precise coordinates are not sent to LLM APIs unless `TERRASCOUT_SEND_PRECISE_COORDINATES_TO_LLM=true`.

## Scientific limitations

- Public DEM/LiDAR coverage is incomplete.
- Bare-earth models still contain vegetation, water, and classification artifacts.
- Agriculture, roads, drainage, and processing stripes produce geometric anomalies.
- Absence from OSM or web literature does not mean a place is unknown.
- Do not use this software to plan looting, trespass, or excavation.

## Architecture

See `docs/architecture.md`, `docs/ethics.md`, `docs/experiments.md`, and `docs/roadmap.md`.

## License

MIT for original TerraScout code. USGS 3DEP data remains in the public domain under USGS terms.
