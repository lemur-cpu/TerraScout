from __future__ import annotations

from pathlib import Path

from terra_scout.dashboard import pages_coverage


def test_coverage_constants_and_imports() -> None:
    assert pages_coverage.COVERAGE_DEFAULT_ROOT == Path("output/coverage")
    assert pages_coverage.COVERAGE_TABLE_LIMIT == 200
    assert pages_coverage.COVERAGE_STALE_RUNNING_SECONDS > 0
    assert callable(pages_coverage.render_coverage)


def test_render_coverage_runs_without_streamlit_ui(tmp_path: Path, monkeypatch) -> None:
    """Smoke-test orchestration with a stub Streamlit module."""
    import types

    calls: list[str] = []

    class _Metric:
        def metric(self, *_args, **_kwargs) -> None:
            calls.append("metric")

    class _StubStreamlit(_Metric):
        def subheader(self, *_a, **_k) -> None:
            pass

        def caption(self, *_a, **_k) -> None:
            pass

        def columns(self, n: int):
            return [_Metric() for _ in range(n)]

        def number_input(self, *_a, **_k):
            return 1

        def button(self, *_a, **_k) -> bool:
            return False

        def dataframe(self, *_a, **_k) -> None:
            pass

        def rerun(self) -> None:
            pass

        session_state = types.SimpleNamespace()

    stub = _StubStreamlit()
    monkeypatch.setattr(pages_coverage, "st", stub)
    root = tmp_path / "cov"
    pages_coverage.render_coverage(root=root, switch_explore=lambda: calls.append("explore"))
    counts_path = root / "coverage.sqlite3"
    assert counts_path.exists()