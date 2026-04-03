from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    NOTE = "note"
    WARNING = "warning"
    ERROR = "error"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Location(BaseModel):
    path: str
    line: int = 1
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None


class Finding(BaseModel):
    rule_id: str
    title: str
    message: str
    severity: Severity
    confidence: Confidence
    location: Location
    fingerprint: str
    suggestion: str | None = None
    evidence: str | None = None
    tags: list[str] = Field(default_factory=list)


class ScanStats(BaseModel):
    scanned_files: int = 0
    findings: int = 0
    rule_errors: int = 0
    suppressed: int = 0


class ScanResult(BaseModel):
    version: str = "1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    repo_root: str
    stats: ScanStats
    findings: list[Finding] = Field(default_factory=list)
