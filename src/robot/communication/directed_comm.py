"""Directed communication module mirroring Java logic."""

from __future__ import annotations

import json

from robot.communication.communication import Communication
from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient


class DirectedCommunication(Communication):
    def __init__(self, robot_id: int, mqtt_client: RobotMqttClient):
        super().__init__(robot_id, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self._subscribe("COMMUNICATION_IN_DIR", f"comm/in/direct/{robot_id}")

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def send_message(self, msg: str) -> None:
        obj = {"id": self.robot_id, "msg": msg}
        self.robot_mqtt_client.publish("comm/out/direct", json.dumps(obj))

    def send_message_with_distance(self, msg: str, distance: int) -> None:
        obj = {"id": self.robot_id, "msg": msg, "dist": distance}
        self.robot_mqtt_client.publish("comm/out/direct", json.dumps(obj))

    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("COMMUNICATION_IN_DIR"):
            robot.communication_interrupt(msg)
        else:
            print(f"Received (unknown dir): {topic}> {msg}")
