from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

TNM_PRODUCTS_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"
IMAGE_SERVER_EXPORT_URL = (
    "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/"
    "ImageServer/exportImage"
)
DEFAULT_DATASETS = (
    "Digital Elevation Model (DEM) 1 meter",
    "National Elevation Dataset (NED) 1/3 arc-second",
    "National Elevation Dataset (NED) 1 arc-second",
)
EPT_INDEX_URL = (
    "https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson"
)
class DownloadLimitExceeded(RuntimeError):
    """A download exceeded the configured megabyte cap."""


class UsgsProduct(BaseModel):
    title: str
    dataset: str
    download_url: str | None = None
    publication_date: str | None = None
    source_crs: str | None = None
    format_name: str | None = None
    bounding_box: list[float] | None = None
    metadata: dict = Field(default_factory=dict)


def search_usgs_products(
    west: float,
    south: float,
    east: float,
    north: float,
    *,
    max_results: int = 20,
    timeout_seconds: float = 30.0,
) -> list[UsgsProduct]:
    """Search TNM Access. Empty lists are valid: coverage is not universal."""
    bbox = f"{west},{south},{east},{north}"
    products: list[UsgsProduct] = []
    seen: set[str] = set()
    for dataset in DEFAULT_DATASETS:
        response = httpx.get(
            TNM_PRODUCTS_URL,
            params={
                "bbox": bbox,
                "datasets": dataset,
                "prodFormats": "GeoTIFF",
                "outputFormat": "JSON",
                "max": str(max_results),
            },
            timeout=timeout_seconds,
            headers={"User-Agent": "terra-scout/0.1 (research; local)"},
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("items") or []:
            url = item.get("downloadURL")
            key = url or item.get("title") or repr(item)
            if key in seen:
                continue
            seen.add(key)
            products.append(
                UsgsProduct(
                    title=str(item.get("title") or "untitled"),
                    dataset=str(item.get("datasets") or dataset),
                    download_url=url,
                    publication_date=item.get("publicationDate"),
                    format_name=item.get("format"),
                    bounding_box=_bbox_from_item(item),
                    metadata={
                        "moreInfo": item.get("moreInfo"),
                        "sourceId": item.get("sourceId"),
                        "size": item.get("sizeInBytes"),
                    },
                )
            )
    return products


def download_3dep_subset(
    west: float,
    south: float,
    east: float,
    north: float,
    *,
    output_dir: Path,
    max_megabytes: float,
    width_pixels: int = 400,
    height_pixels: int = 300,
    timeout_seconds: float = 120.0,
) -> Path:
    """Download a small 3DEP ImageServer GeoTIFF. Aborts over the size cap."""
    if max_megabytes <= 0:
        raise DownloadLimitExceeded("max_megabytes must be positive")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    params = {
        "bbox": f"{west},{south},{east},{north}",
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width_pixels},{height_pixels}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    }
    max_bytes = int(max_megabytes * 1024 * 1024)
    _assert_head_within_limit(params, max_bytes, timeout_seconds)
    destination = output_dir / _subset_filename(west, south, east, north)
    headers = {"User-Agent": "terra-scout/0.1 (research; local)"}
    response = None
    last_error: Exception | None = None
    for _attempt in range(3):
        try:
            response = httpx.get(
                IMAGE_SERVER_EXPORT_URL,
                params=params,
                timeout=timeout_seconds,
                headers=headers,
                follow_redirects=True,
            )
            if response.status_code >= 500:
                last_error = httpx.HTTPStatusError(
                    f"3DEP export failed with {response.status_code}",
                    request=response.request,
                    response=response,
                )
                continue
            response.raise_for_status()
            break
        except httpx.HTTPError as error:
            last_error = error
            response = None
    if response is None:
        raise RuntimeError(f"3DEP export failed after retries: {last_error}")
    content_type = response.headers.get("content-type", "")
    if "json" in content_type and "tiff" not in content_type:
        raise RuntimeError(f"3DEP export returned JSON instead of GeoTIFF: {content_type}")
    if len(response.content) > max_bytes:
        raise DownloadLimitExceeded(
            f"3DEP download exceeded the {max_megabytes} megabyte cap"
        )
    destination.write_bytes(response.content)
    _tag_observation_kind(destination)
    return destination


def _assert_head_within_limit(
    params: dict[str, str],
    max_bytes: int,
    timeout_seconds: float,
) -> None:
    try:
        head = httpx.head(
            IMAGE_SERVER_EXPORT_URL,
            params=params,
            timeout=timeout_seconds,
            headers={"User-Agent": "terra-scout/0.1 (research; local)"},
            follow_redirects=True,
        )
    except httpx.HTTPError:
        return
    length = head.headers.get("content-length")
    if not length:
        return
    if int(length) > max_bytes:
        raise DownloadLimitExceeded(
            f"3DEP Content-Length {int(length)} bytes exceeds the megabyte cap"
        )


def _subset_filename(west: float, south: float, east: float, north: float) -> str:
    def fmt(value: float) -> str:
        return f"{value:.4f}".replace(".", "p").replace("-", "m")

    return f"usgs_3dep_{fmt(west)}_{fmt(south)}_{fmt(east)}_{fmt(north)}.tif"


def _bbox_from_item(item: dict) -> list[float] | None:
    bounding_box = item.get("boundingBox") or item.get("extent")
    if isinstance(bounding_box, dict):
        try:
            return [
                float(bounding_box["minX"]),
                float(bounding_box["minY"]),
                float(bounding_box["maxX"]),
                float(bounding_box["maxY"]),
            ]
        except (KeyError, TypeError, ValueError):
            return None
    return None


def _tag_observation_kind(path: Path) -> None:
    import rasterio

    try:
        with rasterio.open(path, "r+") as dataset:
            dataset.update_tags(TERRASCOUT_OBSERVATION_KIND="usgs_3dep")
    except rasterio.RasterioIOError:
        return


def ept_index_url() -> str:
    return EPT_INDEX_URL


def host_is_allowed(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host.endswith("nationalmap.gov") or host.endswith("usgs.gov")
