# Slice A — Home + Scan completeness

**Status:** approved via operator “build slice a” (2026-11-14)  
**Branch:** `cursor/slice-a-home-94ce` from `cursor/continent-coverage-94ce`  
**Roadmap:** `2026-11-14-operator-loop-roadmap.md` Slice A

## Done when

1. **Home** is the default land page: one composition explaining Scan → Swarm → Review → Explore; ethics banner; CTAs that navigate to those modes.
2. **Scan** (Coverage renamed in nav) shows **% complete** = `(scanned + skipped) / total_cell_count * 100`, plus existing counts.
3. **Region chips** on Scan: Seed demo region; enqueue custom WGS84 bbox (four floats + Enqueue).
4. **CTAs:** Scan · Swarm · Explore · Review — Swarm/Review pages are honest stubs pointing at Slice B/C (CLI swarm / Investigate until those land). No fake swarm UI.

## Non-goals

- Live swarm monitor (B), flagged queue gates (C), Explore viz polish (D)
- Continent candidate pin map; cloud workers

## Builder calls

- Pure helper `coverage_completeness(counts: dict) -> float` in `coverage/progress.py`
- Nav titles: Home, Scan, Swarm, Review, Explore, Briefing, Investigate (Briefing/Investigate stay for power users)
- Home default=`True`; Coverage page title **Scan**