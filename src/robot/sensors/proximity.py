"""Proximity sensor implementation."""

import json
import threading
from typing import List, Optional


class ProximityTimeout(TimeoutError):
    pass


class ProximityReading:
    """
    Container for proximity data returned by the simulator.

    The Java docs indicate the response depends on the requested angles and may
    include distances and optional color codes; at minimum we keep distances
    and
    raw fields so higher layers can parse colors if present. [See doc note]
    """

    def __init__(self, distances: List[int], raw: str):
        self._distances = distances
        self._raw = raw

    def distances(self) -> List[int]:
        return self._distances

    def raw(self) -> str:
        return self._raw


class ProximitySensor:
    """
    Proximity sensor emulation using the Pera-Swarm MQTT protocol.

    Request topic:
        /sensor/proximity
        Payload JSON: {
            "id": <robot_id>, "angles": [int, ...], "reality": <optional>
        }
    Response topic:
        /sensor/proximity/{robot_id}
        Payload: space separated values; for N angles, the first N numbers
        are distances.
        Example (angles [-90,0,90]): "5 10 5 #404040 #000000 #FF0000"
        [docs]  [3]

    This class subscribes to the response topic, publishes requests,
    and returns parsed distances in the order of configured angles.
    """

    REQ_TOPIC = "/sensor/proximity"
    RESP_TOPIC_TMPL = "/sensor/proximity/{robot_id}"

    def __init__(
        self,
        robot_id: int,
        robot_mqtt,
        angles: Optional[List[int]] = None,
        timeout_s: float = 2.0,
    ):
        """
        :param robot_id: numeric robot id used by the simulator
        :param robot_mqtt: RobotMQTT helper with publish(), subscribe(), and
            message dispatch
        :param angles: list of angles (degrees) like [-90, 0, 90]
        :param timeout_s: maximum seconds to wait for a response
        """
        self.robot_id = robot_id
        self._robot_mqtt = robot_mqtt
        self._angles = list(angles) if angles is not None else [-90, 0, 90]
        self._timeout_s = timeout_s

        # Sync primitives
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._latest_raw: str = ""
        self._latest_distances: List[int] = []

        # Subscribe to the response topic from simulator
        resp_topic = self.RESP_TOPIC_TMPL.format(robot_id=self.robot_id)
        self._robot_mqtt.subscribe(resp_topic)

        # Register handler with RobotMQTT if it supports registration;
        # otherwise RobotMQTT should forward all messages to handle_incoming().
        if hasattr(self._robot_mqtt, "add_handler"):
            self._robot_mqtt.add_handler(resp_topic, self._on_message)

    # Optional: Java API parity
    def set_angles(self, angles: List[int]):
        with self._lock:
            self._angles = list(angles)

    def get_angles(self) -> List[int]:
        with self._lock:
            return list(self._angles)

    # RobotMQTT can call this to route messages here
    # if no add_handler() exists.
    def handle_incoming(self, topic: str, payload: str):
        self._on_message(topic, payload)

    # Internal: MQTT callback
    def _on_message(self, topic: str, payload: str):
        expected = self.RESP_TOPIC_TMPL.format(robot_id=self.robot_id)
        if topic != expected:
            return

        # Example response: "5 10 5 #404040 #000000 #FF0000"
        tokens = payload.strip().split()
        # First len(angles) tokens are distances
        with self._lock:
            k = len(self._angles)
            try:
                distances = list(map(int, tokens[:k]))
            except ValueError:
                distances = []
            self._latest_distances = distances
            self._latest_raw = payload
            self._event.set()

    def get_proximity(
        self, reality: Optional[str] = None, timeout_s: Optional[float] = None
    ) -> ProximityReading:
        """
        Request proximity readings and block until reply or timeout.

        :param reality: optional reality selector passed through to simulator
        :param timeout_s: override default timeout for this call
        :return: ProximityReading with distances in angle order
        :raises ProximityTimeout: if response not received in time
        """
        tmo = self._timeout_s if timeout_s is None else timeout_s

        # Clear any previous signal
        self._event.clear()
        with self._lock:
            angles = list(self._angles)

        # Publish request
        payload = {"id": self.robot_id, "angles": angles}
        if reality is not None:
            payload["reality"] = reality
        self._robot_mqtt.publish(self.REQ_TOPIC, json.dumps(payload))

        # Wait for response
        if not self._event.wait(tmo):
            raise ProximityTimeout(
                f"Proximity request timed out after {tmo:.2f}s"
            )

        with self._lock:
            distances = list(self._latest_distances)
            raw = self._latest_raw
            # Prepare for next call
            self._event.clear()

        return ProximityReading(distances=distances, raw=raw)
