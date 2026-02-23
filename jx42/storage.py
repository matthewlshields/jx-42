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
from .models import (
    AuditEvent,
    FinanceLedgerEntry,
    MarketDataPoint,
    MemoryItem,
    PolicyDecisionType,
    RiskLevel,
)

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
                # Escape LIKE metacharacters in the user-supplied query so that
                # literal '%' and '_' characters are not treated as wildcards.
                escaped = query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                cursor = conn.execute(
                    "SELECT * FROM memory_items"
                    " WHERE lower(content) LIKE ? ESCAPE '\\'"
                    " ORDER BY timestamp, item_id LIMIT ?",
                    (f"%{escaped}%", limit),
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


# ---------------------------------------------------------------------------
# SQLite FinanceLedger store
# ---------------------------------------------------------------------------

_FINANCE_LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS finance_ledger (
    entry_id            TEXT PRIMARY KEY,
    date                TEXT NOT NULL,
    amount              REAL NOT NULL,
    currency            TEXT NOT NULL,
    account_id          TEXT NOT NULL,
    merchant            TEXT,
    category            TEXT,
    category_confidence REAL,
    memo                TEXT,
    source              TEXT,
    import_batch_id     TEXT
);
CREATE INDEX IF NOT EXISTS idx_ledger_account ON finance_ledger(account_id);
CREATE INDEX IF NOT EXISTS idx_ledger_date ON finance_ledger(date);
"""


class SqliteFinanceLedger:
    """Persistent finance ledger backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_FINANCE_LEDGER_DDL)

    def save(self, entries: List[FinanceLedgerEntry]) -> None:
        """Persist entries, silently skipping duplicates (idempotent on entry_id)."""
        with self._connect() as conn:
            for e in entries:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO finance_ledger
                        (entry_id, date, amount, currency, account_id,
                         merchant, category, category_confidence,
                         memo, source, import_batch_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        e.entry_id, e.date, e.amount, e.currency, e.account_id,
                        e.merchant, e.category, e.category_confidence,
                        e.memo, e.source, e.import_batch_id,
                    ),
                )

    def load_all(self) -> List[FinanceLedgerEntry]:
        """Return all ledger entries ordered by date then entry_id."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM finance_ledger ORDER BY date, entry_id"
            )
            return [_row_to_ledger_entry(row) for row in cursor.fetchall()]


def _row_to_ledger_entry(row: sqlite3.Row) -> FinanceLedgerEntry:
    return FinanceLedgerEntry(
        entry_id=row["entry_id"],
        date=row["date"],
        amount=row["amount"],
        currency=row["currency"],
        account_id=row["account_id"],
        merchant=row["merchant"] or "",
        category=row["category"] or "uncategorized",
        category_confidence=row["category_confidence"] or 0.0,
        memo=row["memo"] or "",
        source=row["source"] or "bank_export",
        import_batch_id=row["import_batch_id"] or "",
    )


# ---------------------------------------------------------------------------
# SQLite MarketData store
# ---------------------------------------------------------------------------

_MARKET_DATA_DDL = """
CREATE TABLE IF NOT EXISTS market_data (
    symbol  TEXT NOT NULL,
    date    TEXT NOT NULL,
    open    REAL NOT NULL,
    high    REAL NOT NULL,
    low     REAL NOT NULL,
    close   REAL NOT NULL,
    volume  REAL NOT NULL,
    PRIMARY KEY (symbol, date)
);
CREATE INDEX IF NOT EXISTS idx_market_symbol ON market_data(symbol);
"""


class SqliteMarketDataStore:
    """Persistent market data store backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_MARKET_DATA_DDL)

    def save(self, points: List[MarketDataPoint]) -> None:
        """Persist data points, silently skipping duplicates (idempotent on symbol+date)."""
        with self._connect() as conn:
            for p in points:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO market_data
                        (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (p.symbol, p.date, p.open, p.high, p.low, p.close, p.volume),
                )

    def load_all(self) -> List[MarketDataPoint]:
        """Return all market data points ordered by symbol then date."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM market_data ORDER BY symbol, date"
            )
            return [_row_to_market_data_point(row) for row in cursor.fetchall()]


def _row_to_market_data_point(row: sqlite3.Row) -> MarketDataPoint:
    return MarketDataPoint(
        symbol=row["symbol"],
        date=row["date"],
        open=row["open"],
        high=row["high"],
        low=row["low"],
        close=row["close"],
        volume=row["volume"],
    )

