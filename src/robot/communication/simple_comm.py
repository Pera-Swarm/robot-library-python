"""Simple communication module mirroring Java logic."""

from __future__ import annotations

import json
from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.mqtt.mqtt_msg import MqttMsg
from robot.communication.communication import Communication


class SimpleCommunication(Communication):
    def __init__(self, robot_id: int, mqtt_client: RobotMqttClient):
        super().__init__(robot_id, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self._subscribe("COMMUNICATION_IN_SIMP", f"comm/in/simple/{robot_id}")

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def send_message(self, msg: str) -> None:
        obj = {"id": self.robot_id, "msg": msg}
        self.robot_mqtt_client.publish("comm/out/simple", json.dumps(obj))

    def send_message_with_distance(self, msg: str, distance: int) -> None:
        obj = {"id": self.robot_id, "msg": msg, "dist": distance}
        self.robot_mqtt_client.publish("comm/out/simple", json.dumps(obj))

    # IMqttHandler
    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("COMMUNICATION_IN_SIMP"):
            robot.communication_interrupt(msg)
        else:
            expected_topic = self._topics_sub.get("COMMUNICATION_IN_SIMP")
            print(
                f"Received (unknown simp): expected '{expected_topic}', "
                f"but got '{topic}' with message '{msg}'"
            )
