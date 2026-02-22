from __future__ import annotations

import re
from dataclasses import replace
from typing import List, Optional

from .models import AuditEvent

_SECRET_PATTERNS = [
    re.compile(r"(password\s*[:=]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(token\s*[:=]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(api[_-]?key\s*[:=]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(secret\s*[:=]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(sk-[A-Za-z0-9]{8,})"),
]


class AuditLog:
    def append(self, event: AuditEvent) -> str:
        raise NotImplementedError

    def list_events(self, correlation_id: Optional[str] = None) -> List[AuditEvent]:
        raise NotImplementedError


class InMemoryAuditLog(AuditLog):
    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def append(self, event: AuditEvent) -> str:
        redacted = _redact_event(event)
        self._events.append(redacted)
        return redacted.event_id

    def list_events(self, correlation_id: Optional[str] = None) -> List[AuditEvent]:
        if correlation_id is None:
            return list(self._events)
        return [event for event in self._events if event.correlation_id == correlation_id]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _redact_event(event: AuditEvent) -> AuditEvent:
    return replace(
        event,
        inputs_summary=redact_text(event.inputs_summary),
        outputs_summary=redact_text(event.outputs_summary),
    )
