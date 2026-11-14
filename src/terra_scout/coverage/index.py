from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from terra_scout.coverage.grid import (
    demo_seed_tiles,
    tile_bbox_for_id,
    tiles_intersecting,
    total_cell_count,
)

STATUSES = frozenset({"queued", "running", "scanned", "skipped", "failed"})


@dataclass(frozen=True)
class TileRecord:
    tile_id: str
    west: float
    south: float
    east: float
    north: float
    status: str
    updated_at: str
    study_dir: str | None
    message: str | None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class CoverageIndex:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.db_path = self.root / "coverage.sqlite3"

    def init(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tiles (
                    tile_id TEXT PRIMARY KEY,
                    west REAL NOT NULL,
                    south REAL NOT NULL,
                    east REAL NOT NULL,
                    north REAL NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    study_dir TEXT,
                    message TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_tiles_status ON tiles(status);
                """
            )
        return self.db_path

    def _connect(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_record(self, row: sqlite3.Row) -> TileRecord:
        return TileRecord(
            tile_id=row["tile_id"],
            west=row["west"],
            south=row["south"],
            east=row["east"],
            north=row["north"],
            status=row["status"],
            updated_at=row["updated_at"],
            study_dir=row["study_dir"],
            message=row["message"],
        )

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {name: 0 for name in STATUSES}
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM tiles GROUP BY status"
            ).fetchall()
            total_recorded = 0
            for row in rows:
                status = str(row["status"])
                n = int(row["n"])
                total_recorded += n
                if status in counts:
                    counts[status] = n
                else:
                    counts[status] = n
        counts["unscanned"] = max(0, total_cell_count() - total_recorded)
        return counts

    def list_tiles(self, *, limit: int = 500) -> list[TileRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tiles
                ORDER BY updated_at DESC, tile_id
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def enqueue(self, tile_id: str, *, allow_scanned: bool = False) -> bool:
        west, south, east, north = tile_bbox_for_id(tile_id)
        now = _utc_now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM tiles WHERE tile_id = ?",
                (tile_id,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO tiles (
                        tile_id, west, south, east, north,
                        status, updated_at, study_dir, message
                    ) VALUES (?, ?, ?, ?, ?, 'queued', ?, NULL, NULL)
                    """,
                    (tile_id, west, south, east, north, now),
                )
                conn.commit()
                return True
            status = str(row["status"])
            if status in {"queued", "running"}:
                return False
            if status == "scanned" and not allow_scanned:
                return False
            conn.execute(
                """
                UPDATE tiles
                SET status = 'queued', updated_at = ?, message = NULL
                WHERE tile_id = ?
                """,
                (now, tile_id),
            )
            conn.commit()
            return True

    def enqueue_demo_seed(self, *, allow_scanned: bool = False) -> int:
        added = 0
        for tile_id in demo_seed_tiles():
            if self.enqueue(tile_id, allow_scanned=allow_scanned):
                added += 1
        return added

    def enqueue_bbox(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        *,
        allow_scanned: bool = False,
    ) -> int:
        added = 0
        for tile_id in tiles_intersecting(west, south, east, north):
            if self.enqueue(tile_id, allow_scanned=allow_scanned):
                added += 1
        return added

    def mark_status(
        self,
        tile_id: str,
        status: str,
        *,
        study_dir: Path | str | None = None,
        message: str | None = None,
    ) -> None:
        if status not in STATUSES:
            raise ValueError(f"unknown status: {status}")
        now = _utc_now()
        study = str(study_dir) if study_dir is not None else None
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tiles
                SET status = ?, updated_at = ?, study_dir = ?, message = ?
                WHERE tile_id = ?
                """,
                (status, now, study, message, tile_id),
            )
            conn.commit()

    def reset_stale_running(self, stale_seconds: float) -> int:
        if stale_seconds <= 0:
            return 0
        cutoff = (datetime.now(UTC) - timedelta(seconds=stale_seconds)).replace(
            microsecond=0
        ).isoformat()
        now = _utc_now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tiles
                SET status = 'queued', updated_at = ?, message = 'stale running reset'
                WHERE status = 'running' AND updated_at < ?
                """,
                (now, cutoff),
            )
            conn.commit()
            return int(cursor.rowcount)

    def dequeue_queued(self) -> TileRecord | None:
        now = _utc_now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM tiles
                WHERE status = 'queued'
                ORDER BY updated_at, tile_id
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE tiles
                SET status = 'running', updated_at = ?
                WHERE tile_id = ?
                """,
                (now, row["tile_id"]),
            )
            conn.commit()
            refreshed = conn.execute(
                "SELECT * FROM tiles WHERE tile_id = ?",
                (row["tile_id"],),
            ).fetchone()
        if refreshed is None:
            return None
        return self._row_to_record(refreshed)