"""Color sensor implementation."""

import json
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class ColorReading:
    r: int
    g: int
    b: int
    ambient: int


class ColorSensorTimeout(TimeoutError):
    pass


class ColorSensor:
    """
    Color sensor using Pera‑Swarm MQTT topics.

    Request:
      Topic: /sensor/color
      Payload: {"id": <robotID>, "reality": <optional>}
    Response:
      Topic: /sensor/color/{robotID}
      Payload (string): "{R} {G} {B} {ambient}"
    """

    REQ_TOPIC = "/sensor/color"
    RESP_TOPIC_TMPL = "/sensor/color/{robot_id}"

    def __init__(self, robot_id: int, robot_mqtt, timeout_s: float = 2.0):
        self.robot_id = robot_id
        self._robot_mqtt = robot_mqtt
        self._timeout_s = timeout_s

        # Sync + state
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._latest: Optional[ColorReading] = None

        # Subscribe to response topic
        resp_topic = self.RESP_TOPIC_TMPL.format(robot_id=self.robot_id)
        self._robot_mqtt.subscribe(resp_topic)

        # If the RobotMQTT helper allows handler registration, attach directly
        if hasattr(self._robot_mqtt, "add_handler"):
            self._robot_mqtt.add_handler(resp_topic, self._on_mqtt_message)

    # If RobotMQTT doesn’t support handler registration,
    # it should dispatch to this
    def handle_incoming(self, topic: str, payload: str):
        self._on_mqtt_message(topic, payload)

    # Internal: parse simulator reply
    def _on_mqtt_message(self, topic: str, payload: str):
        expected = self.RESP_TOPIC_TMPL.format(robot_id=self.robot_id)
        if topic != expected:
            return

        parts = payload.strip().split()
        if len(parts) < 4:
            return
        try:
            r, g, b, ambient = map(int, parts[:4])
        except ValueError:
            return

        with self._lock:
            self._latest = ColorReading(r=r, g=g, b=b, ambient=ambient)
            self._event.set()

    def request_color(self, reality: Optional[str] = None):
        """
        Send a request without blocking; response will update internal cache.
        """
        payload = {"id": self.robot_id}
        if reality is not None:
            payload["reality"] = int(reality)
        self._robot_mqtt.publish(self.REQ_TOPIC, json.dumps(payload))

    def get_color(
        self, reality: Optional[str] = None, timeout_s: Optional[float] = None
    ) -> ColorReading:
        """
        Request a reading and block until response or timeout.
        """
        tmo = self._timeout_s if timeout_s is None else timeout_s
        self._event.clear()
        self.request_color(reality=reality)

        if not self._event.wait(tmo):
            raise ColorSensorTimeout(f"ColorSensor timed out after {tmo:.2f}s")

        with self._lock:
            self._event.clear()
            assert self._latest is not None
            return self._latest

    def last_color(self) -> Optional[ColorReading]:
        """
        Return the most recently cached reading without making a request.
        """
        with self._lock:
            return self._latest
