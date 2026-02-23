"""Tests for SQLite-backed persistent storage."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jx42.models import AuditEvent, MemoryItem, PolicyDecisionType, RiskLevel
from jx42.storage import SqliteAuditLog, SqliteMemoryLibrarian


def _make_event(event_id: str = "e1", correlation_id: str = "c1") -> AuditEvent:
    return AuditEvent(
        event_id=event_id,
        timestamp="2026-01-01T00:00:00+00:00",
        correlation_id=correlation_id,
        component="kernel",
        action_type="plan_created",
        risk_level=RiskLevel.LOW,
        inputs_summary="test input",
        outputs_summary="test output",
        policy_decision=PolicyDecisionType.ALLOW,
        rationale="test",
    )


def _make_item(item_id: str = "m1") -> MemoryItem:
    return MemoryItem(
        item_id=item_id,
        timestamp="2026-01-01T00:00:00+00:00",
        item_type="preference",
        content="user prefers concise responses",
        provenance="user:manual",
    )


class TestSqliteAuditLog(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._db = Path(self._tmp.name) / "test.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_append_and_list(self) -> None:
        log = SqliteAuditLog(self._db)
        e1 = _make_event("e1", "c1")
        e2 = _make_event("e2", "c1")
        log.append(e1)
        log.append(e2)
        events = log.list_events()
        self.assertEqual(2, len(events))

    def test_filter_by_correlation_id(self) -> None:
        log = SqliteAuditLog(self._db)
        log.append(_make_event("e1", "c1"))
        log.append(_make_event("e2", "c2"))
        events = log.list_events(correlation_id="c1")
        self.assertEqual(1, len(events))
        self.assertEqual("e1", events[0].event_id)

    def test_idempotent_append(self) -> None:
        """Appending the same event twice should not create a duplicate."""
        log = SqliteAuditLog(self._db)
        e = _make_event()
        log.append(e)
        log.append(e)
        self.assertEqual(1, len(log.list_events()))

    def test_redaction_applied(self) -> None:
        log = SqliteAuditLog(self._db)
        e = _make_event()
        # Override inputs_summary with a secret-containing string
        import dataclasses

        e_secret = dataclasses.replace(e, inputs_summary="token=supersecret123")
        log.append(e_secret)
        events = log.list_events()
        self.assertNotIn("supersecret123", events[0].inputs_summary)
        self.assertIn("[REDACTED]", events[0].inputs_summary)

    def test_persistence_across_instances(self) -> None:
        """Data written by one instance is readable by a new instance."""
        log1 = SqliteAuditLog(self._db)
        log1.append(_make_event("e1"))
        log2 = SqliteAuditLog(self._db)
        events = log2.list_events()
        self.assertEqual(1, len(events))
        self.assertEqual("e1", events[0].event_id)

    def test_roundtrip_fields(self) -> None:
        log = SqliteAuditLog(self._db)
        e = _make_event()
        log.append(e)
        events = log.list_events()
        stored = events[0]
        self.assertEqual(e.event_id, stored.event_id)
        self.assertEqual(e.correlation_id, stored.correlation_id)
        self.assertEqual(e.component, stored.component)
        self.assertEqual(e.action_type, stored.action_type)
        self.assertEqual(e.risk_level, stored.risk_level)
        self.assertEqual(e.policy_decision, stored.policy_decision)
        self.assertEqual(e.rationale, stored.rationale)


class TestSqliteMemoryLibrarian(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._db = Path(self._tmp.name) / "test.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_store_and_retrieve_all(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        lib.store([_make_item("m1"), _make_item("m2")])
        items = lib.retrieve()
        self.assertEqual(2, len(items))

    def test_retrieve_with_query(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        lib.store([
            _make_item("m1"),
            MemoryItem("m2", "2026-01-01T00:00:00+00:00", "goal", "retire at 62", "user:chat"),
        ])
        items = lib.retrieve(query="retire")
        self.assertEqual(1, len(items))
        self.assertEqual("m2", items[0].item_id)

    def test_idempotent_store(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        item = _make_item()
        lib.store([item])
        lib.store([item])
        self.assertEqual(1, len(lib.retrieve()))

    def test_limit(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        lib.store([_make_item(f"m{i}") for i in range(5)])
        items = lib.retrieve(limit=3)
        self.assertEqual(3, len(items))

    def test_invalid_limit(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        with self.assertRaises(ValueError):
            lib.retrieve(limit=-1)

    def test_persistence_across_instances(self) -> None:
        lib1 = SqliteMemoryLibrarian(self._db)
        lib1.store([_make_item("m1")])
        lib2 = SqliteMemoryLibrarian(self._db)
        items = lib2.retrieve()
        self.assertEqual(1, len(items))
        self.assertEqual("m1", items[0].item_id)

    def test_roundtrip_fields(self) -> None:
        lib = SqliteMemoryLibrarian(self._db)
        item = _make_item()
        lib.store([item])
        stored = lib.retrieve()[0]
        self.assertEqual(item.item_id, stored.item_id)
        self.assertEqual(item.item_type, stored.item_type)
        self.assertEqual(item.content, stored.content)
        self.assertEqual(item.provenance, stored.provenance)

    def test_like_wildcard_not_injected(self) -> None:
        """Literal % and _ in a query must not be treated as LIKE wildcards."""
        lib = SqliteMemoryLibrarian(self._db)
        lib.store([
            MemoryItem("m1", "2026-01-01T00:00:00+00:00", "note", "100% complete", "user"),
            MemoryItem("m2", "2026-01-01T00:00:00+00:00", "note", "progress update", "user"),
        ])
        # A query of "%" as a wildcard would match both items; as a literal it should match only m1
        items = lib.retrieve(query="100%")
        self.assertEqual(1, len(items))
        self.assertEqual("m1", items[0].item_id)

    def test_underscore_not_injected(self) -> None:
        """Literal _ in a query must not be treated as a single-char wildcard."""
        lib = SqliteMemoryLibrarian(self._db)
        lib.store([
            MemoryItem("m1", "2026-01-01T00:00:00+00:00", "note", "user_preference", "user"),
            MemoryItem("m2", "2026-01-01T00:00:00+00:00", "note", "other note", "user"),
        ])
        # "_" as a wildcard would match any single char and could over-match
        items = lib.retrieve(query="user_preference")
        self.assertEqual(1, len(items))
        self.assertEqual("m1", items[0].item_id)


class TestSqliteFinanceLedger(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._db = Path(self._tmp.name) / "test.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_save_and_load(self) -> None:
        from jx42.models import FinanceLedgerEntry
        from jx42.storage import SqliteFinanceLedger

        store = SqliteFinanceLedger(self._db)
        entry = FinanceLedgerEntry(
            entry_id="e1", date="2026-01-05", amount=-100.0, currency="USD",
            account_id="checking", merchant="Kroger", category="groceries",
            category_confidence=0.9, memo="", source="bank_export", import_batch_id="b1",
        )
        store.save([entry])
        rows = store.load_all()
        self.assertEqual(1, len(rows))
        self.assertEqual("e1", rows[0].entry_id)
        self.assertAlmostEqual(-100.0, rows[0].amount)

    def test_idempotent_save(self) -> None:
        from jx42.models import FinanceLedgerEntry
        from jx42.storage import SqliteFinanceLedger

        store = SqliteFinanceLedger(self._db)
        entry = FinanceLedgerEntry("e1", "2026-01-05", -50.0, "USD", "checking")
        store.save([entry])
        store.save([entry])
        self.assertEqual(1, len(store.load_all()))

    def test_persistence_across_instances(self) -> None:
        from jx42.models import FinanceLedgerEntry
        from jx42.storage import SqliteFinanceLedger

        SqliteFinanceLedger(self._db).save([
            FinanceLedgerEntry("e1", "2026-01-05", -50.0, "USD", "checking"),
        ])
        rows = SqliteFinanceLedger(self._db).load_all()
        self.assertEqual(1, len(rows))


class TestSqliteMarketDataStore(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._db = Path(self._tmp.name) / "test.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_save_and_load(self) -> None:
        from jx42.models import MarketDataPoint
        from jx42.storage import SqliteMarketDataStore

        store = SqliteMarketDataStore(self._db)
        p = MarketDataPoint("AAPL", "2026-01-02", 150.0, 152.0, 149.0, 151.0, 1_000_000)
        store.save([p])
        rows = store.load_all()
        self.assertEqual(1, len(rows))
        self.assertEqual("AAPL", rows[0].symbol)
        self.assertAlmostEqual(151.0, rows[0].close)

    def test_idempotent_save(self) -> None:
        from jx42.models import MarketDataPoint
        from jx42.storage import SqliteMarketDataStore

        store = SqliteMarketDataStore(self._db)
        p = MarketDataPoint("AAPL", "2026-01-02", 150.0, 152.0, 149.0, 151.0, 1_000_000)
        store.save([p])
        store.save([p])
        self.assertEqual(1, len(store.load_all()))

    def test_persistence_across_instances(self) -> None:
        from jx42.models import MarketDataPoint
        from jx42.storage import SqliteMarketDataStore

        SqliteMarketDataStore(self._db).save([
            MarketDataPoint("AAPL", "2026-01-02", 150.0, 152.0, 149.0, 151.0, 1_000_000),
        ])
        rows = SqliteMarketDataStore(self._db).load_all()
        self.assertEqual(1, len(rows))


if __name__ == "__main__":
    unittest.main()
