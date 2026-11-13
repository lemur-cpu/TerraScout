# TerraScout

Evidence-driven research software for finding *potential* anthropogenic landscape features in public LiDAR and digital elevation models.

Anomaly detection is **not** archaeological confirmation. High anomaly scores are residual/shape statistics, not calibrated probabilities that a feature is a site. Human review is required before any discovery claim.

## Current status

Phase 1 (working foundation) is the first deliverable: local DEM analysis, relief visualizations, conventional anomaly detection, CLI, tests, and a real public USGS 3DEP demonstration. Later phases add USGS acquisition UX, a localhost dashboard, a typed agent swarm, and a benchmark harness.

## Scientific limitations

- Public DEM/LiDAR coverage is incomplete. Empty search results are valid.
- Bare-earth models can still contain vegetation, water, or classification artifacts.
- Modern agriculture, roads, drainage, and processing stripes produce geometric anomalies.
- Absence from OSM or web literature does not mean a place is unknown to archaeologists or Indigenous communities.
- This software must not be used to plan looting, trespass, or excavation.

## Quick start

```bash
git clone <repo-url> terra-scout
cd terra-scout
uv sync --extra dev
uv run pytest
```

Analyze a local DEM (no API key):

```bash
uv run terra-scout analyze --dem path/to/dem.tif --output-dir output/demo
```

Expected outputs in `output/demo/`:

- `layers/hillshade.tif`, `layers/slope_degrees.tif`, `layers/local_relief.tif`
- `candidates.geojson`
- `preview_hillshade.png`
- `map.html`

Live USGS subset (size-capped, documented study clip):

```bash
uv run terra-scout datasets search --bbox "-90.07,38.655,-90.055,38.665"
uv run terra-scout datasets download --bbox "-90.07,38.655,-90.055,38.665" --max-megabytes 20 --output-dir data/cache
```

## CLI

| Command | Purpose |
|---|---|
| `terra-scout analyze --dem FILE --output-dir DIR` | Terrain layers + candidates |
| `terra-scout datasets search --bbox minx,miny,maxx,maxy` | USGS TNM + 3DEP coverage |
| `terra-scout datasets download --bbox ... --max-megabytes N` | Size-capped 3DEP export |
| `terra-scout agents run --dem FILE --study-area FILE` | Typed swarm (LLM optional) |
| `terra-scout dashboard` | Localhost Streamlit UI |
| `terra-scout benchmark --config FILE` | Experiment harness |

## Ethics

Precise candidate coordinates stay on the local machine. The dashboard binds to `127.0.0.1`. Do not publish unpublished site maps.

## License

MIT for original TerraScout code. Upstream geospatial datasets keep their own licenses (typically USGS public domain for 3DEP).
