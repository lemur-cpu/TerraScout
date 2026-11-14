from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from terra_scout.coverage.grid import (
    demo_seed_tiles,
    parse_tile_id,
    tile_bbox,
    tile_id,
    tiles_intersecting,
    total_cell_count,
)

STATUSES = frozenset({"queued", "running", "scanned", "skipped", "failed"})


class CoverageIndexError(RuntimeError):
    """Coverage SQLite index could not be opened or updated."""


@dataclass(frozen=True)
class TileRow:
    tile_id: str
    ix: int
    iy: int
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
    def __init__(self, path_to_sqlite_file: Path | str) -> None:
        self.db_path = Path(path_to_sqlite_file)

    def ensure_open(self) -> Path:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tiles (
                    tile_id TEXT PRIMARY KEY,
                    ix INTEGER NOT NULL,
                    iy INTEGER NOT NULL,
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
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.Error as error:
            raise CoverageIndexError(f"cannot open coverage index: {self.db_path}") from error
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_tile(self, row: sqlite3.Row) -> TileRow:
        return TileRow(
            tile_id=row["tile_id"],
            ix=int(row["ix"]),
            iy=int(row["iy"]),
            west=row["west"],
            south=row["south"],
            east=row["east"],
            north=row["north"],
            status=row["status"],
            updated_at=row["updated_at"],
            study_dir=row["study_dir"],
            message=row["message"],
        )

    def persisted_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM tiles").fetchone()
        return int(row["n"]) if row is not None else 0

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {name: 0 for name in STATUSES}
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM tiles GROUP BY status"
            ).fetchall()
            for row in rows:
                status = str(row["status"])
                n = int(row["n"])
                if status in counts:
                    counts[status] = n
                else:
                    counts[status] = n
        counts["unscanned"] = max(0, total_cell_count() - self.persisted_count())
        return counts

    def list_tiles(self, *, limit: int = 500) -> list[TileRow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tiles
                ORDER BY updated_at DESC, tile_id
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_tile(row) for row in rows]

    def enqueue(self, ix: int, iy: int, *, allow_scanned: bool = False) -> bool:
        tid = tile_id(ix, iy)
        west, south, east, north = tile_bbox(ix, iy)
        now = _utc_now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM tiles WHERE tile_id = ?",
                (tid,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO tiles (
                        tile_id, ix, iy, west, south, east, north,
                        status, updated_at, study_dir, message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, NULL, NULL)
                    """,
                    (tid, ix, iy, west, south, east, north, now),
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
                (now, tid),
            )
            conn.commit()
            return True

    def enqueue_demo_seed(self, *, allow_scanned: bool = False) -> int:
        added = 0
        for tid in demo_seed_tiles():
            ix, iy = parse_tile_id(tid)
            if self.enqueue(ix, iy, allow_scanned=allow_scanned):
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
        for tid in tiles_intersecting(west, south, east, north):
            ix, iy = parse_tile_id(tid)
            if self.enqueue(ix, iy, allow_scanned=allow_scanned):
                added += 1
        return added

    def skip(self, ix: int, iy: int, *, message: str | None = None) -> bool:
        tid = tile_id(ix, iy)
        west, south, east, north = tile_bbox(ix, iy)
        now = _utc_now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM tiles WHERE tile_id = ?",
                (tid,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO tiles (
                        tile_id, ix, iy, west, south, east, north,
                        status, updated_at, study_dir, message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'skipped', ?, NULL, ?)
                    """,
                    (tid, ix, iy, west, south, east, north, now, message),
                )
                conn.commit()
                return True
            conn.execute(
                """
                UPDATE tiles
                SET status = 'skipped', updated_at = ?, message = ?
                WHERE tile_id = ?
                """,
                (now, message, tid),
            )
            conn.commit()
            return True

    def mark_status(
        self,
        tile_id_str: str,
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
                (status, now, study, message, tile_id_str),
            )
            conn.commit()

    def reset_stale_running(self) -> int:
        now = _utc_now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tiles
                SET status = 'queued', updated_at = ?, message = 'stale running reset'
                WHERE status = 'running'
                """,
                (now,),
            )
            conn.commit()
            return int(cursor.rowcount)

    def dequeue_queued(self, n: int = 1) -> list[TileRow]:
        if n <= 0:
            return []
        now = _utc_now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tiles
                WHERE status = 'queued'
                ORDER BY updated_at, tile_id
                LIMIT ?
                """,
                (n,),
            ).fetchall()
            if not rows:
                return []
            for row in rows:
                conn.execute(
                    """
                    UPDATE tiles
                    SET status = 'running', updated_at = ?
                    WHERE tile_id = ?
                    """,
                    (now, row["tile_id"]),
                )
            conn.commit()
            ids = [row["tile_id"] for row in rows]
            refreshed = conn.execute(
                f"""
                SELECT * FROM tiles
                WHERE tile_id IN ({",".join("?" * len(ids))})
                ORDER BY updated_at, tile_id
                """,
                ids,
            ).fetchall()
        return [self._row_to_tile(row) for row in refreshed]