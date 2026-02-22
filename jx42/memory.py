from __future__ import annotations

from typing import Iterable, List, Optional

from .models import MemoryItem


class MemoryLibrarian:
    def store(self, items: Iterable[MemoryItem]) -> List[str]:
        raise NotImplementedError

    def retrieve(self, query: Optional[str] = None, limit: int = 5) -> List[MemoryItem]:
        raise NotImplementedError


class InMemoryMemoryLibrarian(MemoryLibrarian):
    def __init__(self) -> None:
        self._items: List[MemoryItem] = []

    def store(self, items: Iterable[MemoryItem]) -> List[str]:
        stored_ids: List[str] = []
        for item in items:
            self._items.append(item)
            stored_ids.append(item.item_id)
        return stored_ids

    def retrieve(self, query: Optional[str] = None, limit: int = 5) -> List[MemoryItem]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        items = sorted(self._items, key=lambda item: (item.timestamp, item.item_id))
        if query is not None:
            lowered = query.lower()
            items = [item for item in items if lowered in item.content.lower()]
        return items[:limit]
