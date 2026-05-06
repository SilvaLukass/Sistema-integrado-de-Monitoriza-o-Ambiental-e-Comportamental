from __future__ import annotations

from collections import deque
from typing import Deque, List

from ..models import Alert
from .db import Database


class AlertStore:
    def __init__(self, max_items: int = 500, db: Database | None = None) -> None:
        self._items: Deque[Alert] = deque(maxlen=max_items)
        self._db = db

    def add(self, alert: Alert) -> None:
        if self._db is not None:
            self._db.add_alert(alert)
            return
        self._items.appendleft(alert)

    def list(self) -> List[Alert]:
        if self._db is not None:
            return self._db.list_alerts()
        return list(self._items)
