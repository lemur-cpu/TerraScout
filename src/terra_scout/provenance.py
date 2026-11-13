from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ObservationKind = Literal["synthetic", "usgs_3dep", "local_user", "unknown"]


class ProvenanceRecord(BaseModel):
    """Traceable origin for a raster, vector, or derived layer."""

    source_path: Path | None = None
    source_url: str | None = None
    observation_kind: ObservationKind = "unknown"
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processor: str = "terra-scout"
    parameters: dict[str, Any] = Field(default_factory=dict)
    parent_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
