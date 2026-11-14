from __future__ import annotations

from pathlib import Path

from terra_scout.dashboard import copy as dashboard_copy
from terra_scout.dashboard import pages_coverage


def test_coverage_constants_and_imports() -> None:
    assert pages_coverage.COVERAGE_DEFAULT_ROOT == Path("output/coverage")
    assert pages_coverage.COVERAGE_TABLE_LIMIT == 200
    assert callable(pages_coverage.render_coverage)
    assert dashboard_copy.COVERAGE_HEADING
    assert dashboard_copy.COVERAGE_CAPTION
    assert dashboard_copy.COVERAGE_NOTE


def test_app_ast_default_coverage() -> None:
    text = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "terra_scout"
        / "dashboard"
        / "app.py"
    ).read_text(encoding="utf-8")
    assert 'title="Coverage"' in text
    assert "default=True" in text
    assert text.index('title="Coverage"') < text.index("default=True")


def test_render_coverage_runs_without_streamlit_ui(tmp_path: Path, monkeypatch) -> None:
    """Smoke-test orchestration with a stub Streamlit module."""
    import types

    from terra_scout.dashboard import copy as copy_mod

    calls: list[str] = []

    class _Metric:
        def metric(self, *_args, **_kwargs) -> None:
            calls.append("metric")

    class _StubStreamlit(_Metric):
        def subheader(self, *_a, **_k) -> None:
            pass

        def caption(self, *_a, **_k) -> None:
            pass

        def markdown(self, *_a, **_k) -> None:
            pass

        def columns(self, n: int):
            return [_Metric() for _ in range(n)]

        def number_input(self, *_a, **_k):
            return 1

        def checkbox(self, *_a, **_k) -> bool:
            return False

        def button(self, *_a, **_k) -> bool:
            return False

        def multiselect(self, *_a, **_k):
            return []

        def selectbox(self, *_a, **_k):
            opts = _k.get("options") or (_a[1] if len(_a) > 1 else None)
            if opts:
                return opts[0]
            return None

        def info(self, *_a, **_k) -> None:
            pass

        def success(self, *_a, **_k) -> None:
            pass

        def dataframe(self, *_a, **_k) -> None:
            pass

        def rerun(self) -> None:
            pass

        session_state = types.SimpleNamespace()

    stub = _StubStreamlit()
    monkeypatch.setattr(pages_coverage, "st", stub)
    root = tmp_path / "cov"
    pages_coverage.render_coverage(
        root=root,
        switch_explore=lambda: calls.append("explore"),
        copy_mod=copy_mod,
    )
    assert (root / "coverage.sqlite3").exists()