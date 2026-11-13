# Research ethics and security

TerraScout is for responsible remote-sensing research. It is not a looting, trespass, or excavation tool.

## Location sensitivity

Potentially undocumented archaeological features are sensitive even when they are only *candidates*.

- Precise coordinates stay in the local SQLite registry and local GeoJSON under `output/` (gitignored).
- Logs, LLM prompts, and any shared HTML default to redacted or rounded coordinates.
- Do not upload unpublished candidate maps to public GitHub, social media, or hosted dashboards.
- The Streamlit UI binds to `127.0.0.1` by default.

## What the software must not do

- Classify a candidate as a newly discovered archaeological site.
- Treat missing web records as proof that Indigenous communities or archaeologists do not know a place.
- Set `novelty_status` to anything other than `not_demonstrated` (or `synthetic_na` on fixtures) unless literature was actually retrieved.
- Emit instructions for digging, collecting artifacts, or entering land without permission.
- Send precise coordinates to external LLM APIs unless the operator explicitly opts in.

## Human review

Suggested statuses: `unreviewed`, `likely_natural`, `likely_modern`, `needs_research`, `potential_anthropogenic_feature`, `expert_reviewed`, `rejected`.

Expert-reviewed means a qualified archaeologist (and, where appropriate, consultation with relevant Indigenous communities) has looked at the evidence. Software cannot assign that status automatically.

## Law and licenses

Operators must follow archaeological protection statutes, land access rules, and dataset licenses for their jurisdiction. USGS 3DEP data is typically public domain; other sources are not. Record provenance for every raster you keep.
