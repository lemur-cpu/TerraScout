from __future__ import annotations

from pathlib import Path

import yaml


def test_benchmark_writes_machine_readable_scores(tmp_path: Path) -> None:
    from terra_scout.eval.benchmark import run_benchmark

    config_path = tmp_path / "synthetic.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "name": "synthetic-mound",
                "observation_kind": "synthetic",
                "approaches": ["conventional", "single_agent", "swarm"],
            }
        ),
        encoding="utf-8",
    )
    result_path = run_benchmark(config_path=config_path, output_dir=tmp_path / "bench")
    payload = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    assert payload["observation_kind"] == "synthetic"
    assert "conventional" in payload["approaches"]
    assert payload["approaches"]["conventional"]["true_positives"] >= 1
    assert payload["spatial_leakage"] == "none_synthetic_fixture"
