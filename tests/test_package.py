from terra_scout import __version__


def test_package_version_is_pinned_for_reproducible_research() -> None:
    assert __version__ == "0.1.0"
