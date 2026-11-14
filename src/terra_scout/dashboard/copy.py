from __future__ import annotations

PAGE_TITLE = "TerraScout"
HEADING = "TerraScout"
CAPTION = "Local LiDAR / DEM explorer for North America"
WARNING = (
    "Candidates stay on this machine. Do not publish unpublished coordinates. "
    "Terrain anomalies are candidates for review — not confirmed archaeological sites. "
    "A missing literature record is not evidence the place is unknown."
)
HOME_HEADING = "North America operator loop"
HOME_CAPTION = (
    "Scan CONUS tiles, monitor the local agent swarm, review qualified flags (later), "
    "or explore terrain directly on this machine."
)
HOME_LOOP = (
    "**Scan** queues USGS 3DEP tiles on a fixed CONUS grid. "
    "**Swarm** starts or attaches the localhost agent swarm on a scanned study. "
    "**Review** (Slice C) will surface research-gated candidate flags. "
    "**Explore** is the terrain workbench for hillshade, LRM, and geometric detect."
)
HOME_ETHICS = (
    "Anomalies are not confirmed archaeology. Missing inventory or literature records "
    "do not mean a place is a new site."
)
HOME_CTA_SCAN = "Open Scan"
HOME_CTA_SWARM = "Open Swarm"
HOME_CTA_REVIEW = "Review (stub)"
HOME_CTA_EXPLORE = "Open Explore"
SWARM_HEADING = "Swarm monitor"
SWARM_CAPTION = (
    "Start or attach the local six-agent swarm on one scanned study. "
    "Status polls disk — no cloud workers."
)
SWARM_BODY = (
    "Pick a Coverage tile (or DATA PATH study) with a DEM, then **Start** to launch "
    "`terra-scout agents run` as a local subprocess, or **Attach** to read an existing "
    "run. Per-agent rows come from `swarm_run.json` while running and from "
    "`agent_traces.json` when the run finishes writing traces. There is no cloud "
    "worker fleet. Software never auto-sets `expert_reviewed`."
)
SWARM_ETHICS = (
    "Anomaly detection is not archaeological confirmation. Novelty stays "
    "not_demonstrated until literature is retrieved."
)
SWARM_STOP_HELP = (
    "Stop sends SIGTERM (then kill if needed) to the local agents process. "
    "It does not invent partial agent_traces; products already on disk remain. "
    "Traces appear only when a run finishes writing them."
)
SWARM_RESUME_HELP = (
    "Resume means Start again on the same study — a full re-run of agents, "
    "not a silent auto-restart."
)
SWARM_EMPTY = (
    "No runnable studies yet. Scan a Coverage tile "
    "(or set DATA PATH to a study with a DEM)."
)
SWARM_NO_DEM = (
    "Selected study has no resolvable DEM (run_manifest dem_path or *.tif)."
)
SWARM_POLL_SECONDS = 2
REVIEW_HEADING = "Flagged review queue"
REVIEW_CAPTION = "Slice C — not shipped in this release."
REVIEW_BODY = (
    "Research-backed qualification gates and a dedicated review queue land in Slice C. "
    "Until then, use **Investigate** on one study at a time."
)
REVIEW_INVESTIGATE_CTA = "Open Investigate"
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

COVERAGE_HEADING = "Scan — CONUS coverage board"
COVERAGE_CAPTION = (
    "Progressive USGS 3DEP scanning over a fixed CONUS grid. "
    "Queue tiles, process with a download cap, and open studies in Explore."
)
COVERAGE_NOTE = (
    "Anomaly detection is not archaeological confirmation. "
    "Unscanned cells are virtual until enqueued in the sparse index."
)
