# Major dependencies

| Package | Role | License (verify at install) | Why this one | Alternatives | Security notes |
|---|---|---|---|---|---|
| uv | installs / lock | Apache-2.0 / MIT | Fast, reproducible Python 3.12 envs | pip, poetry | Pin via uv.lock |
| numpy / scipy | arrays, filters | BSD | Standard scientific stack | — | No network |
| rasterio | GeoTIFF IO | BSD | Mature GDAL bindings with wheels | osgeo.gdal | Wheels bundle GDAL; system GDAL optional |
| pyproj | CRS | MIT | PROJ for units and reprojection | pycrs | Grid files may download if configured |
| shapely / geopandas | geometry | BSD | Vector ops and GeoJSON | ogr | Validate CRS before overlay |
| scikit-image / OpenCV | morphology, components | BSD / Apache-2.0 | Established CV | PIL-only | Use headless OpenCV |
| pydantic | typed agent I/O | MIT | Fail-fast schemas | attrs | Do not put secrets in models logged to disk |
| typer / rich | CLI | MIT | Clear commands | argparse | — |
| httpx | HTTP | BSD | Timeouts and streaming downloads | requests | TLS verify on; size cap enforced in code |
| sqlalchemy | registry | MIT | SQLite now, PostGIS later | raw sqlite3 | File stays local |
| streamlit / folium | dashboard | Apache-2.0 / MIT | Local research UI | dash, leafmap | Bind localhost; no public deploy of candidates |
| pytest / ruff | test / lint | MIT | CI baseline | unittest, flake8 | Do not skip tests |
| torch (optional) | future models | BSD-style | Requested ML backend | scikit-learn | Do not commit weights |
| pdal (optional) | point clouds | BSD | EPT streaming | laspy | Needs system PDAL; DEM-only must work without it |
| LangGraph (not required) | graphs | MIT | Optional later extra | custom orchestrator | Custom engine is default so tests stay deterministic |

Star counts were not used as a substitute for scientific validation. Specialized libraries (PDAL, rasterio) beat general ones for LiDAR/GIS.
