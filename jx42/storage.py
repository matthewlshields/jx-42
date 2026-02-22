"""SQLite-backed persistent storage for AuditLog and MemoryLibrarian.

Uses only Python stdlib (sqlite3) — no external dependencies.
Thread-safety: each call opens a short-lived connection; suitable for
single-process use (not multi-process concurrent writes).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from .audit import AuditLog, _redact_event
from .memory import MemoryLibrarian
from .models import AuditEvent, MemoryItem, PolicyDecisionType, RiskLevel

# ---------------------------------------------------------------------------
# SQLite AuditLog
# ---------------------------------------------------------------------------

_AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id        TEXT PRIMARY KEY,
    timestamp       TEXT NOT NULL,
    correlation_id  TEXT NOT NULL,
    component       TEXT NOT NULL,
    action_type     TEXT NOT NULL,
    risk_level      TEXT NOT NULL,
    inputs_summary  TEXT NOT NULL,
    outputs_summary TEXT NOT NULL,
    policy_decision TEXT NOT NULL,
    rationale       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id);
"""


class SqliteAuditLog(AuditLog):
    """Persistent append-only audit log backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_AUDIT_DDL)

    def append(self, event: AuditEvent) -> str:
        redacted = _redact_event(event)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO audit_events
                    (event_id, timestamp, correlation_id, component, action_type,
                     risk_level, inputs_summary, outputs_summary, policy_decision, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    redacted.event_id,
                    redacted.timestamp,
                    redacted.correlation_id,
                    redacted.component,
                    redacted.action_type,
                    redacted.risk_level.value,
                    redacted.inputs_summary,
                    redacted.outputs_summary,
                    redacted.policy_decision.value,
                    redacted.rationale,
                ),
            )
        return redacted.event_id

    def list_events(self, correlation_id: Optional[str] = None) -> List[AuditEvent]:
        with self._connect() as conn:
            if correlation_id is None:
                cursor = conn.execute("SELECT * FROM audit_events ORDER BY timestamp, event_id")
            else:
                cursor = conn.execute(
                    "SELECT * FROM audit_events WHERE correlation_id = ? ORDER BY timestamp, event_id",
                    (correlation_id,),
                )
            return [_row_to_audit_event(row) for row in cursor.fetchall()]


def _row_to_audit_event(row: sqlite3.Row) -> AuditEvent:
    return AuditEvent(
        event_id=row["event_id"],
        timestamp=row["timestamp"],
        correlation_id=row["correlation_id"],
        component=row["component"],
        action_type=row["action_type"],
        risk_level=RiskLevel(row["risk_level"]),
        inputs_summary=row["inputs_summary"],
        outputs_summary=row["outputs_summary"],
        policy_decision=PolicyDecisionType(row["policy_decision"]),
        rationale=row["rationale"],
    )


# ---------------------------------------------------------------------------
# SQLite MemoryLibrarian
# ---------------------------------------------------------------------------

_MEMORY_DDL = """
CREATE TABLE IF NOT EXISTS memory_items (
    item_id    TEXT PRIMARY KEY,
    timestamp  TEXT NOT NULL,
    item_type  TEXT NOT NULL,
    content    TEXT NOT NULL,
    provenance TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_items(timestamp);
"""


class SqliteMemoryLibrarian(MemoryLibrarian):
    """Persistent memory store backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_MEMORY_DDL)

    def store(self, items) -> List[str]:  # type: ignore[override]
        stored_ids: List[str] = []
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO memory_items
                        (item_id, timestamp, item_type, content, provenance)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item.item_id, item.timestamp, item.item_type, item.content, item.provenance),
                )
                stored_ids.append(item.item_id)
        return stored_ids

    def retrieve(self, query: Optional[str] = None, limit: int = 5) -> List[MemoryItem]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._connect() as conn:
            if query is None:
                cursor = conn.execute(
                    "SELECT * FROM memory_items ORDER BY timestamp, item_id LIMIT ?",
                    (limit,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM memory_items WHERE lower(content) LIKE ? ORDER BY timestamp, item_id LIMIT ?",
                    (f"%{query.lower()}%", limit),
                )
            return [_row_to_memory_item(row) for row in cursor.fetchall()]


def _row_to_memory_item(row: sqlite3.Row) -> MemoryItem:
    return MemoryItem(
        item_id=row["item_id"],
        timestamp=row["timestamp"],
        item_type=row["item_type"],
        content=row["content"],
        provenance=row["provenance"],
    )
