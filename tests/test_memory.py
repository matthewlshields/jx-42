import unittest

from jx42.memory import InMemoryMemoryLibrarian
from jx42.models import MemoryItem


class TestMemoryLibrarian(unittest.TestCase):
    def test_store_and_retrieve(self) -> None:
        librarian = InMemoryMemoryLibrarian()
        items = [
            MemoryItem(
                item_id="item-1",
                timestamp="2026-01-01T00:00:00+00:00",
                item_type="note",
                content="budget preference",
                provenance="user",
            ),
            MemoryItem(
                item_id="item-2",
                timestamp="2026-01-02T00:00:00+00:00",
                item_type="note",
                content="risk limits",
                provenance="user",
            ),
        ]
        stored_ids = librarian.store(items)
        self.assertEqual(["item-1", "item-2"], stored_ids)
        results = librarian.retrieve(query="risk", limit=5)
        self.assertEqual(1, len(results))
        self.assertEqual("item-2", results[0].item_id)


if __name__ == "__main__":
    unittest.main()
