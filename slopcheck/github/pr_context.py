from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequestContext:
    event_name: str | None
    repository: str | None
    head_sha: str | None
    ref: str | None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> PullRequestContext:
        source = env or os.environ
        return cls(
            event_name=source.get("GITHUB_EVENT_NAME"),
            repository=source.get("GITHUB_REPOSITORY"),
            head_sha=source.get("GITHUB_HEAD_SHA") or source.get("GITHUB_SHA"),
            ref=source.get("GITHUB_REF"),
        )
