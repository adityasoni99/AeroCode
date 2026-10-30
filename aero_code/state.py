"""ProofLoop state machine phases, state model, and synchronous/async event bus."""

import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from aero_code.schemas.issues import IssueReport
from aero_code.schemas.patch import PatchProposal
from aero_code.schemas.report import EvidenceReport
from aero_code.schemas.research import ResearchResult


class ProofLoopPhase(str, Enum):
    """Deterministic stages in the ProofLoop lifecycle."""

    INTAKE = "INTAKE"
    INVESTIGATE = "INVESTIGATE"
    RESEARCH = "RESEARCH"
    REPRODUCE_BASELINE = "REPRODUCE_BASELINE"
    GENERATE_PATCH = "GENERATE_PATCH"
    GIT_GUARD = "GIT_GUARD"
    SANDBOX_EXECUTE = "SANDBOX_EXECUTE"
    EVIDENCE_REPORT = "EVIDENCE_REPORT"
    PUBLISH_PR = "PUBLISH_PR"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProofLoopEvent(BaseModel):
    """An event emitted during ProofLoop pipeline transitions or operations."""

    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    phase: Optional[ProofLoopPhase] = None
    timestamp: float = Field(default_factory=time.time)


class ProofLoopState(BaseModel):
    """Comprehensive state tracking the lifecycle of an Aero-Code bug repair."""

    phase: ProofLoopPhase = ProofLoopPhase.INTAKE
    issue: Optional[IssueReport] = None
    research: Optional[ResearchResult] = None
    patch: Optional[PatchProposal] = None
    report: Optional[EvidenceReport] = None
    retry_count: int = 0
    escalated: bool = False
    history: List[ProofLoopEvent] = Field(default_factory=list)


class ProofLoopEventBus:
    """In-memory publish-subscribe event bus for real-time telemetry and SSE streaming."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[ProofLoopEvent], None]] = []

    def subscribe(self, callback: Callable[[ProofLoopEvent], None]) -> None:
        """Register a subscriber callback."""
        self._subscribers.append(callback)

    def publish(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        phase: Optional[ProofLoopPhase] = None,
    ) -> ProofLoopEvent:
        """Publish an event to all subscribers synchronously."""
        event = ProofLoopEvent(
            event_type=event_type,
            payload=payload or {},
            phase=phase,
            timestamp=time.time(),
        )
        for sub in list(self._subscribers):
            try:
                sub(event)
            except Exception:
                pass
        return event
