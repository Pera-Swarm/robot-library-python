"""MQTT helper functions."""

import json
import time
from typing import Callable, Dict


class RobotMQTT:
    """
    High-level MQTT helper coordinating robot lifecycle, state, and I/O.

    Management topics (robot <-> simulator/tools):
      Outbound commands (robot -> tools/server):
        - /mgr/out/start   : {"id": <int>}
        - /mgr/out/stop    : {"id": <int>}
        - /mgr/out/reset   : {"id": <int>}
        - /loc/out/pose    : {"id": <int>, "x": <float>, "y": <float>, 
                              "heading": <float>}

      Inbound management (tools/server -> robot):
        - /mgr/in/{robot_id} : "START" | "STOP" | "RESET" | 
          JSON {"cmd": "...", ...}

    Sensor/comm helpers can register per-topic handlers via add_handler().
    """

    # Outbound topics
    START_OUT = "/mgr/out/start"
    STOP_OUT = "/mgr/out/stop"
    RESET_OUT = "/mgr/out/reset"
    POSE_OUT = "/loc/out/pose"

    # Inbound topics
    MGR_IN_TMPL = "/mgr/in/{robot_id}"

    def __init__(self, robot_id, mqtt_client, coordinate):
        self.robot_id = int(robot_id)
        self.client = mqtt_client
        self.coordinate = coordinate

        # Pluggable message handlers keyed by exact topic
        self._handlers: Dict[str, Callable[[str, str], None]] = {}

        # Subscribe to management inbox
        inbox = self.MGR_IN_TMPL.format(robot_id=self.robot_id)
        self.client.subscribe(inbox)

        # If underlying client supports per-topic handler registration, fine.
        # Otherwise, Robot.mqtt dispatches to handle_incoming() which demuxes.
        if hasattr(self.client, "add_handler"):
            self.client.add_handler(inbox, self._handle_mgr)

    # Allow helpers (sensors/comm/indicators) to register callbacks
    def add_handler(self, topic: str, callback: Callable[[str, str], None]):
        self._handlers[topic] = callback
        self.client.subscribe(topic)

    # Optional removal
    def remove_handler(self, topic: str):
        self._handlers.pop(topic, None)
        if hasattr(self.client, "unsubscribe"):
            self.client.unsubscribe(topic)

    # ------------- High-level commands -------------

    def start(self):
        self.client.publish(self.START_OUT, json.dumps({"id": self.robot_id}))

    def stop(self):
        self.client.publish(self.STOP_OUT, json.dumps({"id": self.robot_id}))

    def reset(self):
        self.client.publish(self.RESET_OUT, json.dumps({"id": self.robot_id}))

    def publish_coordinate(self, coordinate=None):
        c = coordinate or self.coordinate
        payload = {
            "id": self.robot_id,
            "x": float(c.x),
            "y": float(c.y),
            "heading": float(c.heading),
            "ts": time.time(),
        }
        self.client.publish(self.POSE_OUT, json.dumps(payload))

    # ------------- Incoming message routing -------------

    def handle_incoming(self, topic, payload):
        """
        Entry point used by Robot.run() to deliver all inbound MQTT messages.
        Routes to registered handlers, then management handler
        if the topic matches.
        """
        # First route to any exact-match helper
        cb = self._handlers.get(topic)
        if cb:
            cb(topic, payload)
            return

        # Management inbox
        inbox = self.MGR_IN_TMPL.format(robot_id=self.robot_id)
        if topic == inbox:
            self._handle_mgr(topic, payload)

    def _handle_mgr(self, _topic, payload):
        """
        Handle management commands from tools/simulator:
        Accepts simple strings START/STOP/RESET or JSON {"cmd":"START"}.
        """
        cmd = payload.strip()
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict) and "cmd" in obj:
                cmd = str(obj["cmd"]).upper()
        except Exception:
            cmd = cmd.upper()

        if cmd == "START":
            # Upstream expects robot to move to RUN state; 
            # publish ack if needed
            # Actual state change is handled by the Robot subclass logic.
            return
        if cmd == "STOP":
            return
        if cmd == "RESET":
            # Often used to reinitialize pose; forward a fresh pose broadcast
            self.publish_coordinate()
            return
        # Unknown management commands can be ignored or logged.