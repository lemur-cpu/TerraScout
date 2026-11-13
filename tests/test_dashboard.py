from __future__ import annotations

from pathlib import Path

import pytest

from terra_scout.analyze import analyze_dem


def test_dashboard_loader_reports_empty_directory(tmp_path: Path) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory

    state = load_analysis_directory(tmp_path)
    assert state.status == "empty"
    assert "No analysis" in state.message


def test_dashboard_loader_reads_analyze_outputs(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory
    from terra_scout.dashboard.review import evidence_packet

    output_dir = tmp_path / "out"
    analyze_dem(synthetic_dem_path, output_dir)
    state = load_analysis_directory(output_dir)
    assert state.status == "ok"
    assert state.candidate_count >= 1
    assert state.hillshade_png is not None
    assert state.map_path is not None and state.map_path.exists()
    assert "local_relief" in state.layer_paths
    assert "slope_degrees" in state.layer_paths
    assert "tpi" in state.layer_paths
    assert state.candidates
    assert state.observation_kind == "synthetic"
    assert state.status_counts.get("unreviewed", 0) >= 1
    assert "unreviewed" in state.message.lower()
    assert "candidate site" in state.message.lower()
    assert "not archaeological confirmation" in state.message.lower()
    packet = evidence_packet(state.candidates[0])
    assert packet["novelty_status"] == "synthetic_na"
    assert "geometry_wkt" not in packet
    assert "candidate site" in str(packet["claim"]).lower()
    assert "not a calibrated archaeological probability" in packet["score_definition"].lower()
    from terra_scout.registry.store import CandidateStore

    registry = CandidateStore(output_dir / "registry.sqlite3")
    candidate = registry.list_candidates()[0]
    updated = registry.set_review_status(candidate.candidate_id, "needs_research")
    assert updated.review_status == "needs_research"
    refreshed = load_analysis_directory(output_dir)
    assert refreshed.status_counts.get("needs_research") == 1
    assert refreshed.status_counts.get("unreviewed", 0) == 0


def test_queue_message_names_candidate_sites() -> None:
    from terra_scout.dashboard.loader import queue_message

    message = queue_message({"unreviewed": 3}, 5)
    assert "3 unreviewed of 5 candidate sites" in message
    assert "not archaeological confirmation" in message.lower()


def test_evidence_packet_omits_geometry_and_states_novelty() -> None:
    from terra_scout.dashboard.review import evidence_packet
    from terra_scout.detection.models import CandidateFeature
    from terra_scout.provenance import ProvenanceRecord

    packet = evidence_packet(
        CandidateFeature(
            candidate_id="c1",
            feature_category="mound_like",
            geometry_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
            crs_epsg=32615,
            area_m2=10.0,
            perimeter_m=4.0,
            circularity=0.8,
            elongation=1.1,
            orientation_degrees=0.0,
            elevation_contrast_m=1.0,
            local_slope_degrees=2.0,
            anomaly_score=2.4,
            detection_method="test",
            observation_kind="local_user",
            novelty_status="not_demonstrated",
            novelty_note=(
                "Literature was not retrieved. Novelty is not demonstrated. "
                "A missing record is not proof the place is unknown."
            ),
            provenance=ProvenanceRecord(observation_kind="local_user"),
        )
    )
    assert packet["novelty_status"] == "not_demonstrated"
    assert "not demonstrated" in packet["novelty_note"].lower()
    assert "not proof" in packet["novelty_note"].lower()
    assert "geometry_wkt" not in packet
    assert "POLYGON" not in str(packet.values())
    assert packet["anomaly_score"] == 2.4


def test_ranked_queue_orders_by_score_descending() -> None:
    from terra_scout.dashboard.review import rank_candidates
    from terra_scout.detection.models import CandidateFeature
    from terra_scout.provenance import ProvenanceRecord

    def _stub(candidate_id: str, score: float) -> CandidateFeature:
        return CandidateFeature(
            candidate_id=candidate_id,
            feature_category="mound_like",
            geometry_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
            crs_epsg=32615,
            area_m2=10.0,
            perimeter_m=4.0,
            circularity=0.8,
            elongation=1.1,
            orientation_degrees=0.0,
            elevation_contrast_m=1.0,
            local_slope_degrees=2.0,
            anomaly_score=score,
            detection_method="test",
            observation_kind="synthetic",
            provenance=ProvenanceRecord(observation_kind="synthetic"),
        )

    ranked = rank_candidates([_stub("low", 1.0), _stub("high", 4.0), _stub("mid", 2.5)])
    assert [item.candidate_id for item in ranked] == ["high", "mid", "low"]


def test_overlay_renders_selected_candidate_on_relief_layer(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.analyze import analyze_dem
    from terra_scout.dashboard.loader import load_analysis_directory
    from terra_scout.dashboard.review import render_layer_with_candidates

    output_dir = tmp_path / "out"
    analyze_dem(synthetic_dem_path, output_dir)
    state = load_analysis_directory(output_dir)
    selected = state.candidates[0].candidate_id
    figure = render_layer_with_candidates(
        state.layer_paths["local_relief"],
        state.candidates,
        selected,
    )
    assert figure.axes
    assert figure.axes[0].has_data()
    assert figure.get_facecolor()[:3] == pytest.approx((19 / 255, 21 / 255, 15 / 255), abs=0.02)


def test_finder_copy_does_not_auto_claim_sites() -> None:
    from terra_scout.dashboard.copy import (
        ABOUT,
        CAPTION,
        HEADING,
        LOOP_CAPTION,
        SKEPTIC_EMPTY,
        WARNING,
    )

    assert "candidate site finder" in HEADING.lower()
    assert "human confirms" in CAPTION.lower()
    assert "not a new site" in WARNING.lower()
    assert "novelty is not demonstrated" in ABOUT.lower()
    assert "scan" in LOOP_CAPTION.lower() and "human" in LOOP_CAPTION.lower()
    assert "skeptic" in SKEPTIC_EMPTY.lower()
    assert "analyze-only" in SKEPTIC_EMPTY.lower()


def test_console_theme_uses_field_terminal_tokens() -> None:
    from terra_scout.dashboard.theme import CONSOLE_CSS, PHOSPHOR_AMBER, TERMINAL_BG

    assert PHOSPHOR_AMBER == "#E4B44C"
    assert TERMINAL_BG == "#13150F"
    assert "Share Tech Mono" in CONSOLE_CSS
    assert "IBM Plex Mono" in CONSOLE_CSS
    assert PHOSPHOR_AMBER in CONSOLE_CSS
    assert "prefers-reduced-motion" in CONSOLE_CSS
    assert "stDeployButton" in CONSOLE_CSS or "DeployButton" in CONSOLE_CSS
