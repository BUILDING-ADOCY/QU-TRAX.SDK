"""
A minimal event bus for publishing and subscribing to dynamic graph events.
Example usage:
    from src.qtrax.utils.event_bus import EventBus

    def on_edge_blocked(data):
        print("Edge blocked: ", data)

    EventBus.subscribe("edge_blocked", on_edge_blocked)
    EventBus.publish("edge_blocked", {"source": 2, "target": 3})
"""

from typing import Callable, Dict, List, Any

class EventBus:
    _subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe callback(data) to events of type event_name.
        """
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        cls._subscribers[event_name].append(callback)

    @classmethod
    def unsubscribe(cls, event_name: str, callback: Callable[[Any], None]) -> None:
        """
        Remove a callback from an event’s subscriber list.
        """
        if event_name in cls._subscribers:
            cls._subscribers[event_name].remove(callback)

    @classmethod
    def publish(cls, event_name: str, data: Any) -> None:
        """
        Notify all subscribers to this event_name with data.
        """
        for callback in cls._subscribers.get(event_name, []):
            callback(data)