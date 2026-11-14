from __future__ import annotations

from pathlib import Path

from terra_scout.dashboard import copy as dashboard_copy


def test_home_copy_ethics_and_ctas() -> None:
    assert "not confirmed archaeolog" in dashboard_copy.HOME_ETHICS.lower()
    assert "new site" in dashboard_copy.HOME_ETHICS.lower()
    assert dashboard_copy.HOME_CTA_SCAN
    assert dashboard_copy.HOME_CTA_SWARM
    assert "stub" not in dashboard_copy.HOME_CTA_SWARM.lower()
    assert dashboard_copy.HOME_CTA_REVIEW
    assert dashboard_copy.HOME_CTA_EXPLORE
    assert "local" in dashboard_copy.SWARM_BODY.lower()
    assert "slice c" in dashboard_copy.REVIEW_BODY.lower()
    assert dashboard_copy.COVERAGE_HEADING.startswith("Scan")


def test_app_home_is_default_landing() -> None:
    text = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "terra_scout"
        / "dashboard"
        / "app.py"
    ).read_text(encoding="utf-8")
    assert 'title="Home"' in text
    assert 'title="Scan"' in text
    assert 'title="Swarm"' in text
    assert 'title="Review"' in text
    assert "default=True" in text
    home_idx = text.index('title="Home"')
    default_idx = text.index("default=True")
    assert home_idx < default_idx