"""Simple communication module."""

import json
import queue
import threading
from typing import Callable, Optional


class SimpleCommunication:
    """
    Simple (broadcast-like) inter-robot comms.

    Publish (robot -> server):
      Topic: /comm/out/simple
      Payload: {"id": <int>, "msg": "<string>", "dist": <optional number>}

    Subscribe (server -> robot):
      Topic: /comm/in/simple/{robot_id}
      Payload: "<string>"  (server delivers message body)
    """

    OUT_TOPIC = "/comm/out/simple"
    IN_TOPIC_TMPL = "/comm/in/simple/{robot_id}"

    def __init__(self, robot_id: int, robot_mqtt):
        self.robot_id = robot_id
        self._mqtt = robot_mqtt

        # inbound queue and optional callback
        self._in_q: "queue.Queue[str]" = queue.Queue()
        self._cb: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()

        # subscribe to inbox
        in_topic = self.IN_TOPIC_TMPL.format(robot_id=self.robot_id)
        self._mqtt.subscribe(in_topic)
        if hasattr(self._mqtt, "add_handler"):
            self._mqtt.add_handler(in_topic, self._on_message)

    # If RobotMQTT doesn’t provide add_handler, it should forward to this
    def handle_incoming(self, topic: str, payload: str):
        self._on_message(topic, payload)

    def _on_message(self, topic: str, payload: str):
        expected = self.IN_TOPIC_TMPL.format(robot_id=self.robot_id)
        if topic != expected:
            return
        self._in_q.put(payload)
        with self._lock:
            if self._cb:
                try:
                    self._cb(payload)
                except Exception:
                    pass

    # API

    def set_callback(self, fn: Callable[[str], None]):
        with self._lock:
            self._cb = fn

    def send(self, message: str, distance: float | None = None):
        """
        Send a message via the simple protocol; server decides receivers.
        """
        data = {"id": self.robot_id, "msg": message}
        if distance is not None:
            data["dist"] = distance
        self._mqtt.publish(self.OUT_TOPIC, json.dumps(data))

    def recv_nowait(self) -> Optional[str]:
        try:
            return self._in_q.get_nowait()
        except queue.Empty:
            return None

    def recv(self, timeout: float | None = None) -> Optional[str]:
        try:
            return (
                self._in_q.get(timeout=timeout)
                if timeout is not None
                else self._in_q.get()
            )
        except queue.Empty:
            return None
