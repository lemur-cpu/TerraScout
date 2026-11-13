from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_search_usgs_products_returns_empty_list_when_api_has_no_items() -> None:
    from terra_scout.data.usgs import search_usgs_products

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 0, "items": []}
    mock_response.raise_for_status = MagicMock()

    with patch("terra_scout.data.usgs.httpx.get", return_value=mock_response) as mocked:
        products = search_usgs_products(-90.07, 38.655, -90.055, 38.665)
    assert products == []
    mocked.assert_called()


def test_download_3dep_subset_refuses_oversize_payload(tmp_path: Path) -> None:
    from terra_scout.data.usgs import DownloadLimitExceeded, download_3dep_subset

    mock_head = MagicMock()
    mock_head.status_code = 200
    mock_head.headers = {"content-length": str(80 * 1024 * 1024), "content-type": "image/tiff"}
    mock_head.raise_for_status = MagicMock()

    with patch("terra_scout.data.usgs.httpx.head", return_value=mock_head):
        with pytest.raises(DownloadLimitExceeded, match="megabyte"):
            download_3dep_subset(
                -90.07,
                38.655,
                -90.055,
                38.665,
                output_dir=tmp_path,
                max_megabytes=20,
            )
