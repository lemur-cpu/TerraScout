# Experiments

The benchmark harness compares three approaches on the **same** tools and study area:

1. Conventional geospatial / computer-vision detection only.
2. A single research LLM using those tools.
3. The six-agent swarm.

Metrics: precision, recall, false-positive rate, per-category detection, runtime, memory, token cost, and a qualitative “skeptic changed the rank” flag.

Spatial leakage: training and evaluation polygons must not overlap. Synthetic fixtures are labeled `observation_kind=synthetic`. Live USGS clips are labeled `observation_kind=usgs_3dep`.

Configs live in `experiments/`. Machine-readable output is JSON under `output/benchmarks/` (gitignored).
