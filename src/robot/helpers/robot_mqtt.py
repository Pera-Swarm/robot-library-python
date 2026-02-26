from __future__ import annotations

import json

from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient


class RobotMQTT:
    def __init__(self, robot_id: int, mqtt: RobotMqttClient, reality: str):
        self.robot_mqtt_client = mqtt
        self.robot_id = robot_id
        self.reality = reality

        self._topics_sub: dict[str, str] = {}
        self._subscribe("ROBOT_MSG", f"robot/msg/{robot_id}")
        self._subscribe("ROBOT_MSG_BROADCAST", "robot/msg/broadcast")

    def robot_create(self, x: float, y: float, heading: float) -> None:
        msg = {
            "id": self.robot_id,
            "x": x,
            "y": y,
            "heading": heading,
            "reality": self.reality,
        }
        self.robot_mqtt_client.publish("robot/create", json.dumps(msg))

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic in (
            self._topics_sub.get("ROBOT_MSG"),
            self._topics_sub.get("ROBOT_MSG_BROADCAST"),
        ):
            msg_topic = msg.split(" ")[0]
            if msg_topic == "ID?":
                obj = {"id": self.robot_id, "reality": "V"}
                self.robot_mqtt_client.publish("robot/live", json.dumps(obj))
                print(f"robot/live > {json.dumps(obj)}")
            elif msg_topic == "START":
                robot.start()
            elif msg_topic == "STOP":
                robot.stop()
            elif msg_topic == "RESET":
                robot.reset()
        else:
            print(f"Received (unknown): {topic}> {msg}")
