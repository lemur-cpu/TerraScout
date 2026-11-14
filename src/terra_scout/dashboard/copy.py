from __future__ import annotations

PAGE_TITLE = "TerraScout"
HEADING = "TerraScout"
CAPTION = "Local LiDAR / DEM explorer for North America"
WARNING = (
    "Candidates stay on this machine. Do not publish unpublished coordinates. "
    "Terrain anomalies are candidates for review — not confirmed archaeological sites. "
    "A missing literature record is not a new site."
)
LOOP_CAPTION = "Workflow: scan terrain → rank candidates → review evidence → human decision."
BRIEFING_HEADING = "Briefing"
BRIEFING_CAPTION = (
    "Overview of this study area: what was scanned, candidate counts, and swarm status."
)
EXPLORE_HEADING = "Explore"
EXPLORE_CAPTION = (
    "Walk the terrain layers. Bookmark a place, or run geometric detection on this DEM."
)
INVESTIGATE_HEADING = "Investigate"
INVESTIGATE_CAPTION = (
    "One candidate at a time: evidence packet, specialist notes, and your review status."
)
INSPECTOR_HEADING = "Evidence packet"
QUEUE_CAPTION = (
    "Candidates ranked by anomaly score (a shape/residual statistic, not site probability)."
)
SKEPTIC_EMPTY = (
    "No skeptic notes on this candidate. Analyze-only runs do not run the skeptic agent."
)
TRACES_EMPTY = (
    "No specialist traces yet. Run `terra-scout agents` to attach the six-agent report."
)
DEM_MISSING = (
    "DEM path not found. Set DEM PATH in the sidebar, or re-run analyze/agents "
    "so run_manifest.json records the DEM."
)
ABOUT = (
    "TerraScout helps you find and review terrain candidate sites from local DEM/LiDAR. "
    "Anomaly detection is not archaeological confirmation. "
    "Novelty is not demonstrated until literature is actually retrieved."
)

ACQUIRE_HEADING = "Acquire study area"
ACQUIRE_CAPTION = (
    "Download a size-capped USGS 3DEP DEM for a North America bounding box, "
    "then run geometric detection into a local output folder."
)
ACQUIRE_NOTE = (
    "Coverage is not universal. Download refuses oversize payloads. "
    "Results are candidate sites for review — not confirmed archaeology."
)
ACQUIRE_DEMO_HELP = "Uses the documented public demo box near St. Louis / Cahokia region."
