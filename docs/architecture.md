# Architecture

TerraScout is a local-first research pipeline, not a chatbot that inspects screenshots.

```
study area / local DEM
        │
        ▼
  data acquisition  ── USGS TNM Access, 3DEP ImageServer, local files
        │                          optional: OpenTopography, NASA CMR, PDAL/EPT
        ▼
  DEM validation  ── CRS, units, nodata, pixel size, provenance
        │
        ▼
  terrain analysis ── hillshade, slope, curvature, LRM, TPI, SVF, TRI
        │
        ▼
  anomaly detection ── morphology + connected components → CandidateFeature
        │
        ▼
  candidate registry ── SQLite geometries, evidence, review status
        │
        ▼
  agent swarm ── geospatial, detection, research, skeptic, verification, reporting
        │
        ▼
  dashboard  ── candidate site finder: rank → evidence packet → human / authority
  CLI / benchmark
```

## Replaceable interfaces

| Module | Interface | Default | Swap |
|---|---|---|---|
| Raster IO | `load_dem` / `write_geotiff` | rasterio | GDAL CLI |
| Terrain | `TerrainLayer` functions of a DEM | numpy/scipy | rvt-py (CPython <3.12) |
| Detection | `Detector.detect(dem, layers) -> list[CandidateFeature]` | statistical CV | future PyTorch segmenter |
| Registry | `CandidateStore` | SQLite | PostGIS |
| LLM | `LanguageModelClient` | none / Ollama | OpenAI-compatible HTTP |
| Orchestration | `Orchestrator.run` | custom typed graph | LangGraph (optional extra) |

## Why not rvt-py as a hard dependency

Relief Visualization Toolbox (Kokalj et al.) is the right scientific reference. Current `rvt-py` on PyPI declares `python <3.12`. TerraScout reimplements the published methods and cites them, so Python 3.12+ stays first-class.

## Data sources (live, not invented)

- USGS TNM Access: `https://tnmaccess.nationalmap.gov/api/v1/products`
- USGS 3DEP ImageServer export: `https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage`
- USGS EPT index: `https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson`
- OpenTopography: requires `OPENTOPOGRAPHY_API_KEY`
- NASA CMR search: `https://cmr.earthdata.nasa.gov/search/` (download needs Earthdata login)

Coverage is not universal. Search must return an empty, explicit result when nothing matches.

## PostGIS migration path

SQLite stores WGS84 WKT plus GeoJSON sidecars. To migrate: run `docs/postgis.md` — enable PostGIS, copy `candidates` rows into `geometry(Polygon, 4326)`, keep the same Pydantic models.

## Security

The dashboard binds to `127.0.0.1` by default. Candidate maps are local files. CI never uploads rasters.
