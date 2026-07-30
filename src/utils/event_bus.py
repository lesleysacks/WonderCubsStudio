"""Small synchronous application event bus."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

EventCallback = Callable[[dict[str, Any]], None]


class EventBus:
    """Publish application events without coupling services to UI widgets."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventCallback]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: EventCallback) -> None:
        """Subscribe once; repeated screen openings remain idempotent."""
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: EventCallback) -> None:
        callbacks = self._subscribers.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self._subscribers.pop(event_name, None)

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        """Notify a snapshot so callbacks may safely unsubscribe."""
        for callback in tuple(self._subscribers.get(event_name, ())):
            callback(payload)
