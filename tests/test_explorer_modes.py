from __future__ import annotations

from pathlib import Path

from terra_scout.analyze import analyze_dem


def test_loader_resolves_agents_products_layout(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory

    run_root = tmp_path / "swarm_run"
    products = run_root / "products"
    analyze_dem(synthetic_dem_path, products)
    (run_root / "swarm_report.md").write_text(
        "# TerraScout swarm report\n\ncandidates: 1\n",
        encoding="utf-8",
    )
    state = load_analysis_directory(run_root)
    assert state.status == "ok"
    assert state.layout_kind == "agents"
    assert state.product_root == products
    assert state.candidates
    assert state.inventory["registry"] is True
    assert state.inventory["swarm_report"] is True
    assert state.inventory["layers"] is True
    assert state.next_unreviewed_id == state.candidates[0].candidate_id


def test_loader_inventory_flags_manifest_and_traces_absence(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory

    output_dir = tmp_path / "out"
    analyze_dem(synthetic_dem_path, output_dir)
    state = load_analysis_directory(output_dir)
    assert state.layout_kind == "analyze"
    assert state.inventory["run_manifest"] is True
    assert state.inventory["agent_traces"] is False
    assert state.inventory["map"] is True


def test_agent_traces_json_round_trip(tmp_path: Path) -> None:
    from terra_scout.agents.schemas import AgentTrace, ToolTrace
    from terra_scout.agents.trace_io import write_agent_traces
    from terra_scout.dashboard.traces import load_agent_traces

    traces = [
        AgentTrace(
            agent_id="geospatial",
            task_id="inspect",
            tool_calls=[
                ToolTrace(
                    tool_name="inspect_dem",
                    output_summary="ok",
                    succeeded=True,
                )
            ],
            notes=["DEM inspected"],
        )
    ]
    path = write_agent_traces(
        tmp_path / "agent_traces.json",
        summary="1 candidate",
        llm_was_used=False,
        candidate_count=1,
        traces=traces,
    )
    loaded = load_agent_traces(path)
    assert loaded is not None
    assert loaded["summary"] == "1 candidate"
    assert loaded["llm_was_used"] is False
    assert loaded["candidate_count"] == 1
    assert loaded["traces"][0]["agent_id"] == "geospatial"
    assert loaded["traces"][0]["notes"] == ["DEM inspected"]


def test_write_report_persists_agent_traces_json(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.agents.orchestrator import run_swarm
    from terra_scout.dashboard.traces import load_agent_traces

    output_dir = tmp_path / "swarm"
    report = run_swarm(
        dem_path=synthetic_dem_path,
        study_area_path=None,
        output_dir=output_dir,
    )
    traces_path = output_dir / "agent_traces.json"
    assert traces_path.exists()
    loaded = load_agent_traces(traces_path)
    assert loaded is not None
    assert loaded["llm_was_used"] == report.llm_was_used
    assert loaded["candidate_count"] == len(report.candidates)
    assert len(loaded["traces"]) >= 6
    agent_ids = {item["agent_id"] for item in loaded["traces"]}
    assert {
        "geospatial",
        "detection",
        "research",
        "skeptic",
        "verification",
        "reporting",
    } <= agent_ids


def test_analyze_writes_run_manifest(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.manifest import load_run_manifest, resolve_dem_path

    output_dir = tmp_path / "out"
    analyze_dem(synthetic_dem_path, output_dir)
    manifest = load_run_manifest(output_dir)
    assert manifest is not None
    assert Path(manifest["dem_path"]) == synthetic_dem_path.resolve()
    assert manifest["observation_kind"] == "synthetic"
    assert resolve_dem_path(output_dir, None) == synthetic_dem_path.resolve()
    assert resolve_dem_path(output_dir, str(tmp_path / "missing.tif")) is None


def test_bookmark_candidate_is_human_nomination(
    synthetic_dem_path: Path,
) -> None:
    from shapely import wkt

    from terra_scout.dashboard.bookmark import BOOKMARK_SCORE_DEFINITION, bookmark_candidate
    from terra_scout.dashboard.review import evidence_packet
    from terra_scout.io.dem import load_dem

    dem = load_dem(synthetic_dem_path)
    minx, miny, maxx, maxy = dem.bounds
    easting = (minx + maxx) / 2
    northing = (miny + maxy) / 2
    candidate = bookmark_candidate(easting=easting, northing=northing, dem=dem)
    assert candidate.detection_method == "human_bookmark"
    assert candidate.anomaly_score == 0.0
    assert candidate.anomaly_score_definition == BOOKMARK_SCORE_DEFINITION
    assert candidate.feature_category == "unknown_anomaly"
    assert candidate.review_status == "unreviewed"
    assert candidate.observation_kind == "synthetic"
    assert candidate.novelty_status == "synthetic_na"
    geom = wkt.loads(candidate.geometry_wkt)
    assert abs(geom.centroid.x - easting) < 1.0
    assert abs(geom.area - (3.141592653589793 * 25.0 * 25.0)) < 50.0
    packet = evidence_packet(candidate)
    assert "geometry_wkt" not in packet
    assert "POLYGON" not in str(packet.values())


def test_geometric_refresh_keeps_human_bookmarks(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.bookmark import bookmark_candidate
    from terra_scout.dashboard.geometric import refresh_geometric_detection
    from terra_scout.io.dem import load_dem
    from terra_scout.registry.store import CandidateStore

    product_root = tmp_path / "out"
    analyze_dem(synthetic_dem_path, product_root)
    store = CandidateStore(product_root / "registry.sqlite3")
    before = store.list_candidates()
    assert before
    old_geometric_ids = {
        item.candidate_id for item in before if item.detection_method != "human_bookmark"
    }
    dem = load_dem(synthetic_dem_path)
    minx, miny, maxx, maxy = dem.bounds
    bookmark = bookmark_candidate(
        easting=(minx + maxx) / 2,
        northing=(miny + maxy) / 2,
        dem=dem,
    )
    store.add_candidates([bookmark])
    refresh_geometric_detection(dem_path=synthetic_dem_path, product_root=product_root)
    after = CandidateStore(product_root / "registry.sqlite3").list_candidates()
    ids = {item.candidate_id for item in after}
    assert bookmark.candidate_id in ids
    assert old_geometric_ids & ids == set()
    assert any(item.detection_method != "human_bookmark" for item in after)
