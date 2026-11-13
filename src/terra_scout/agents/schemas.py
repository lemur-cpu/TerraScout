from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from terra_scout.detection.models import CandidateFeature


class ToolTrace(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    output_summary: str
    succeeded: bool


class Citation(BaseModel):
    title: str
    url: str | None = None
    retrieved: bool = False
    note: str = ""


class FailedRetrieval(BaseModel):
    source: str
    reason: str


class AgentTrace(BaseModel):
    agent_id: str
    task_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool_calls: list[ToolTrace] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    failed_retrievals: list[FailedRetrieval] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    candidate_ids: list[str] = Field(default_factory=list)


class CandidateCritique(BaseModel):
    candidate_id: str
    alternative_explanations: list[str]
    keep_unreviewed: bool = True


class SwarmReport(BaseModel):
    summary: str
    report_path: Path
    agent_traces: list[AgentTrace]
    candidates: list[CandidateFeature]
    llm_was_used: bool
    uncertainties: list[str]
