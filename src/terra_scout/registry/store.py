from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Session

from terra_scout.detection.models import CandidateFeature, ReviewStatus
from terra_scout.provenance import ProvenanceRecord


class Base(DeclarativeBase):
    pass


class CandidateRow(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String, primary_key=True)
    payload_json = Column(Text, nullable=False)
    review_status = Column(String, nullable=False, default="unreviewed")
    geometry_wkt = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CandidateStore:
    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{database_path}")
        Base.metadata.create_all(self.engine)

    def add_candidates(self, candidates: list[CandidateFeature]) -> None:
        with Session(self.engine) as session:
            for candidate in candidates:
                session.merge(
                    CandidateRow(
                        candidate_id=candidate.candidate_id,
                        payload_json=candidate.model_dump_json(),
                        review_status=candidate.review_status,
                        geometry_wkt=candidate.geometry_wkt,
                    )
                )
            session.commit()

    def list_candidates(self) -> list[CandidateFeature]:
        with Session(self.engine) as session:
            rows = session.scalars(select(CandidateRow)).all()
            return [self._to_model(row) for row in rows]

    def get(self, candidate_id: str) -> CandidateFeature:
        with Session(self.engine) as session:
            row = session.get(CandidateRow, candidate_id)
            if row is None:
                raise KeyError(candidate_id)
            return self._to_model(row)

    def set_review_status(self, candidate_id: str, status: ReviewStatus) -> CandidateFeature:
        with Session(self.engine) as session:
            row = session.get(CandidateRow, candidate_id)
            if row is None:
                raise KeyError(candidate_id)
            payload = json.loads(row.payload_json)
            payload["review_status"] = status
            row.payload_json = json.dumps(payload)
            row.review_status = status
            session.commit()
            return self._to_model(row)

    def delete_where_detection_method_not(self, keep: set[str]) -> int:
        """Delete registry rows whose detection_method is outside keep."""
        deleted = 0
        with Session(self.engine) as session:
            rows = list(session.scalars(select(CandidateRow)).all())
            for row in rows:
                payload = json.loads(row.payload_json)
                method = str(payload.get("detection_method", ""))
                if method not in keep:
                    session.delete(row)
                    deleted += 1
            session.commit()
        return deleted

    def _to_model(self, row: CandidateRow) -> CandidateFeature:
        payload = json.loads(row.payload_json)
        payload["review_status"] = row.review_status
        if "provenance" in payload and not isinstance(payload["provenance"], ProvenanceRecord):
            payload["provenance"] = ProvenanceRecord.model_validate(payload["provenance"])
        return CandidateFeature.model_validate(payload)
