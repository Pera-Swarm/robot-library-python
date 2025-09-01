"""Directed communication module."""

import json
import queue
import threading
from typing import Callable, Optional, Tuple


class DirectedCommunication:
    """
    Directed (one-to-one) inter-robot comms.

    Publish (robot -> server):
      Topic: /comm/out/direct
      Payload: {"id": <src>, "to": <dst>, "msg": "<string>"}

    Subscribe (server -> robot):
      Topic: /comm/in/direct/{robot_id}
      Payload: ("{\"from\": <src>, \"msg\": \"...\"}"
               " or plain string per server;");
               this helper normalizes to (src, msg).
    """

    OUT_TOPIC = "/comm/out/direct"
    IN_TOPIC_TMPL = "/comm/in/direct/{robot_id}"

    def __init__(self, robot_id: int, robot_mqtt):
        self.robot_id = robot_id
        self._mqtt = robot_mqtt

        self._in_q: "queue.Queue[Tuple[int, str]]" = queue.Queue()
        self._cb: Optional[Callable[[int, str], None]] = None
        self._lock = threading.Lock()

        inbox = self.IN_TOPIC_TMPL.format(robot_id=self.robot_id)
        self._mqtt.subscribe(inbox)
        if hasattr(self._mqtt, "add_handler"):
            self._mqtt.add_handler(inbox, self._on_message)

    # If RobotMQTT doesn’t provide add_handler, it should route here.
    def handle_incoming(self, topic: str, payload: str):
        self._on_message(topic, payload)

    def _on_message(self, topic: str, payload: str):
        expected = self.IN_TOPIC_TMPL.format(robot_id=self.robot_id)
        if topic != expected:
            return

        # Try JSON with {"from": int, "msg": "..."}; fall back to raw string
        src = -1
        msg = payload
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                src = int(obj.get("from", -1))
                msg = str(obj.get("msg", ""))
        except Exception:
            pass

        self._in_q.put((src, msg))
        with self._lock:
            if self._cb:
                try:
                    self._cb(src, msg)
                except Exception:
                    pass

    # API

    def set_callback(self, fn: Callable[[int, str], None]):
        with self._lock:
            self._cb = fn

    def send(self, to_robot: int, message: str):
        """
        Send directly to a specific robot via the server’s directed comm
        channel.
        """
        data = {"id": self.robot_id, "to": int(to_robot), "msg": message}
        self._mqtt.publish(self.OUT_TOPIC, json.dumps(data))

    def recv_nowait(self) -> Optional[tuple[int, str]]:
        try:
            return self._in_q.get_nowait()
        except queue.Empty:
            return None

    def recv(self, timeout: float | None = None) -> Optional[tuple[int, str]]:
        try:
            if timeout is not None:
                return self._in_q.get(timeout=timeout)
            return self._in_q.get()
        except queue.Empty:
            return None
