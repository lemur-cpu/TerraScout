# TerraScout MVP spec

**Status:** approved by the founding project brief (2026-11-13).

## Problem

Public LiDAR and DEM coverage across North America can reveal anthropogenic landscape features. Guessing from images is not science. TerraScout must detect terrain anomalies, retain uncertainty, and require human expert review.

## Non-goals

- Automated archaeological confirmation or “new site” claims
- Publishing precise unpublished coordinates
- Training an archaeological detector without labeled data
- Unauthorized excavation or land access guidance

## Required capabilities

1. Load and validate a local DEM GeoTIFF (CRS, nodata, units, resolution).
2. Derive hillshade, slope, curvature, local relief, and topographic position.
3. Detect mound-like, linear, and depression anomalies as geospatial candidates with scores that are *not* calibrated archaeological probabilities.
4. Write GeoJSON, PNG previews, and an HTML map from local files.
5. Search USGS TNM Access and download size-capped 3DEP subsets.
6. Store candidates in local SQLite with review status and provenance.
7. Run a localhost Streamlit dashboard on local data.
8. Orchestrate six specialized agents with typed schemas and real tools. LLM is optional.
9. Benchmark conventional detection vs single-agent vs multi-agent on synthetic ground truth, with a separate live DEM demonstration.

## Uncertainty rule

`anomaly_score` is a dimensionless residual/shape statistic. It must never be labeled as P(archaeological) unless a calibration study exists.

## Ethics rule

Precise coordinates stay local. LLM prompts use coarse geography unless `TERRASCOUT_SEND_PRECISE_COORDINATES_TO_LLM=true`.
