from __future__ import annotations

from collections import deque
from typing import Deque, List

from ..models import Alert


class AlertStore:
    def __init__(self, max_items: int = 500) -> None:
        self._items: Deque[Alert] = deque(maxlen=max_items)

    def add(self, alert: Alert) -> None:
        self._items.appendleft(alert)

    def list(self) -> List[Alert]:
        return list(self._items)
