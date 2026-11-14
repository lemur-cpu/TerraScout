# Review workstation dashboard

**Goal:** Replace the Streamlit file dump with a local review workstation: terrain first, ranked candidates, honest scores, human status.

**Architecture:** Keep reading `analyze` products and `CandidateStore`. New helpers in `dashboard/review.py` rank candidates and overlay polygons on a GeoTIFF. `app.py` is layout only. No second detector.

**Spec:** `docs/agents/specs/2026-11-13-terrascout-mvp.md`

## Constraints

- TDD. Incremental commits. DRY. Localhost only.
- Do not dump GeoJSON or coordinates as the primary view.
- Do not celebrate detections. Queue language only.
- Hide Streamlit Deploy.
- `anomaly_score_definition` visible next to the score.

## Tasks

1. Loader returns layers, map, registry candidates, status counts, observation_kind.
2. Overlay helper draws selected candidate on a relief GeoTIFF.
3. Dashboard layout: layer switch + overlay, ranked queue, inspector, local map pane, review control.
4. `.streamlit/config.toml` toolbar viewer mode.
