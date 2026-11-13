from __future__ import annotations

import pytest


def test_require_pdal_fails_fast_when_the_optional_extra_is_missing() -> None:
    from terra_scout.io.pointcloud import PointCloudUnavailable, require_pdal

    try:
        import pdal  # noqa: F401
    except ImportError:
        with pytest.raises(PointCloudUnavailable, match="DEM"):
            require_pdal()
    else:
        require_pdal()
