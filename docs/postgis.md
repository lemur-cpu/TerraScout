# PostGIS migration path

MVP storage is SQLite (`TERRASCOUT_DATABASE_PATH`, default `./var/terra_scout.sqlite3`). Geometries are WGS84 WKT plus optional GeoJSON sidecars. This is enough for a laptop registry.

When a team needs concurrent editors, spatial indexes, or QGIS live layers:

1. Provision PostgreSQL 16+ with PostGIS 3.4+.
2. Create schema `terra_scout` and table `candidates` with `geom geometry(Polygon, 4326)` and GIST index.
3. Copy JSON evidence columns unchanged from SQLite.
4. Point `CandidateStore` at the SQLAlchemy URL `postgresql+psycopg://...` — the store interface does not change.
5. Keep SQLite as a supported backend; do not require PostGIS for the core CLI.

Do not put unpublished coordinates on a network database that is reachable beyond the research team.
