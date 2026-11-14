# Operator-loop handoffs

Self-contained agent briefs for TerraScout slices **B–E** on the NA operator loop. Copy the body below `---` in each file into a new agent session.

| Slice | Handoff | Roadmap “Done when” (summary) |
| --- | --- | --- |
| **B** | [2026-11-14-slice-b-swarm-handoff.md](2026-11-14-slice-b-swarm-handoff.md) | Localhost swarm monitor: start/attach, poll `agent_traces.json`, explicit stop/resume |
| **C** | [2026-11-14-slice-c-review-handoff.md](2026-11-14-slice-c-review-handoff.md) | Review queue listing research-gated `needs_research` / `potential_anthropogenic_feature` flags |
| **D** | [2026-11-14-slice-d-explore-handoff.md](2026-11-14-slice-d-explore-handoff.md) | Explore as LiDAR workbench: Home entry, layer presets, vertical exaggeration, profile tool |
| **E** | [2026-11-14-slice-e-sections-handoff.md](2026-11-14-slice-e-sections-handoff.md) | Optional: coarse section packs (state / 1°) aggregating fine Coverage tiles |

**Authoritative vision:** `docs/agents/specs/2026-11-14-operator-loop-roadmap.md`  
**Slice A (Home + Scan)** ships on `cursor/slice-a-home-94ce`; stack later slices on the branch that includes their dependencies (usually previous slice tip).

**Order:** B → C → D; E only if fine-grid Scan UX is too noisy and operator approves a section-pack spec.