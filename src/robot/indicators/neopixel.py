"""NeoPixel indicator controller."""

import json
import threading
from typing import Iterable, Optional


class NeoPixel:
    """
    NeoPixel indicator controller via MQTT.

    Outbound (robot -> server/simulator):
      Topic: /indicator/out/neopixel
      Payloads:
        {"id": <int>, "cmd": "set", "color": "#RRGGBB"}
        {"id": <int>, "cmd": "pixels", "colors": ["#RRGGBB", ...]}
        {
            "id": <int>,
            "cmd": "blink",
            "color": "#RRGGBB",
            "period_ms": 500,
            "duty": 0.5,
        }
        {"id": <int>, "cmd": "pulse", "color": "#RRGGBB", "period_ms": 1200}
        {"id": <int>, "cmd": "off"}

    Optional inbound acknowledgments (server -> robot):
      Topic: /indicator/in/neopixel/{robot_id}
      Payload: {"ok": true, "cmd": "..."} or a status string
      (ignored if absent).
    """

    OUT_TOPIC = "/indicator/out/neopixel"
    IN_TOPIC_TMPL = "/indicator/in/neopixel/{robot_id}"

    def __init__(
        self,
        robot_id: int,
        robot_mqtt,
        pixel_count: int | None = None,
        subscribe_ack: bool = False,
    ):
        """
        :param robot_id: Robot numeric id
        :param robot_mqtt: RobotMQTT helper for publish/subscribe
            and optional handler registry
        :param pixel_count: Optional number of LEDs for validation
            (None to skip)
        :param subscribe_ack: Subscribe to ack/status messages if simulator
            emits them
        """
        self.robot_id = robot_id
        self._mqtt = robot_mqtt
        self._pixel_count = pixel_count
        self._subscribe_ack = subscribe_ack
        self._lock = threading.Lock()
        self._last_cmd: Optional[dict] = None
        self._closed = False

        if subscribe_ack:
            inbox = self.IN_TOPIC_TMPL.format(robot_id=robot_id)
            self._mqtt.subscribe(inbox)
            if hasattr(self._mqtt, "add_handler"):
                self._mqtt.add_handler(inbox, self._on_ack)

    # Inbound ack handler (optional)
    def _on_ack(self, topic: str, payload: str):
        # Acks are optional; store last payload for debugging
        with self._lock:
            self._last_cmd = {"ack_topic": topic, "ack_payload": payload}

    # ------------- Public API -------------

    def init(self, color: str = "#000000"):
        """Initialize strip to a known color."""
        self.set_color(color)

    def off(self):
        """Turn off the strip."""
        self._send({"cmd": "off"})

    def set_color(self, color: str):
        """Set all pixels to a single color in #RRGGBB."""
        self._validate_hex(color)
        self._send({"cmd": "set", "color": color})

    def set_pixels(self, colors: Iterable[str]):
        """
        Set per-pixel colors.
        :param colors: iterable of #RRGGBB strings
        """
        cols = list(colors)
        for c in cols:
            self._validate_hex(c)
        if self._pixel_count is not None and len(cols) != self._pixel_count:
            raise ValueError(
                f"Expected {self._pixel_count} colors, got {len(cols)}"
            )
        self._send({"cmd": "pixels", "colors": cols})

    def blink(self, color: str, period_ms: int = 500, duty: float = 0.5):
        """
        Blink a solid color with period and duty cycle.
        """
        self._validate_hex(color)
        if period_ms <= 0 or not (0 < duty <= 1):
            raise ValueError("period_ms must be >0 and 0<duty<=1")
        self._send({
            "cmd": "blink",
            "color": color,
            "period_ms": int(period_ms),
            "duty": float(duty),
        })

    def pulse(self, color: str, period_ms: int = 1200):
        """Smooth pulse animation in given color."""
        self._validate_hex(color)
        if period_ms <= 0:
            raise ValueError("period_ms must be > 0")
        self._send({
            "cmd": "pulse",
            "color": color,
            "period_ms": int(period_ms),
        })

    def last_status(self) -> Optional[dict]:
        """Return last recorded ack/status (if subscribed)."""
        with self._lock:
            return dict(self._last_cmd) if self._last_cmd else None

    def close(self):
        """Cleanup subscriptions/resources."""
        if self._subscribe_ack:
            inbox = self.IN_TOPIC_TMPL.format(robot_id=self.robot_id)
            # If RobotMQTT has an unsubscribe, call it; otherwise it’s harmless
            # to leave subscribed.
            if hasattr(self._mqtt, "unsubscribe"):
                self._mqtt.unsubscribe(inbox)
        self._closed = True

    # ------------- Internals -------------

    def _send(self, cmd: dict):
        if self._closed:
            raise RuntimeError("NeoPixel controller is closed")
        payload = {"id": self.robot_id}
        payload.update(cmd)
        self._mqtt.publish(self.OUT_TOPIC, json.dumps(payload))

    @staticmethod
    def _validate_hex(color: str):
        if (
            not isinstance(color, str)
            or len(color) != 7
            or not color.startswith("#")
        ):
            raise ValueError("Color must be a #RRGGBB string")
        int(color[1:], 16)  # raises ValueError on invalid hex
