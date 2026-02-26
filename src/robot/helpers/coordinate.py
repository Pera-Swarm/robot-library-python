from __future__ import annotations

from robot.interfaces import IMqttHandler
from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient


class Coordinate(IMqttHandler):
    def __init__(
        self,
        robot_id: int,
        x: float,
        y: float,
        heading: float,
        mqtt_client: RobotMqttClient,
    ):
        self._x = float(x)
        self._y = float(y)
        self._heading = float(heading)
        self._robot_id = robot_id
        self.robot_mqtt_client = mqtt_client

        # subscriptions
        self._topics_sub: dict[str, str] = {}
        self._subscribe("ROBOT_LOCALIZATION", "localization/update/?")

    # Subscriptions ------------------------------------------------------
    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, robot, message: MqttMsg) -> None:  # noqa: D401
        topic = message.topic
        if topic == self._topics_sub.get("ROBOT_LOCALIZATION"):
            print(f"publishing the localization data of robot {robot.get_id()}")
            self.publish_coordinate()

    # Getters/Setters ----------------------------------------------------
    def get_x(self) -> float:
        return self._x

    def get_y(self) -> float:
        return self._y

    def set_x(self, x: float) -> None:
        self._x = float(x)

    def set_y(self, y: float) -> None:
        self._y = float(y)

    def get_heading(self) -> float:
        return self._heading

    def get_heading_rad(self) -> float:
        import math

        return float(math.radians(self._heading))

    def set_heading(self, heading: float) -> None:
        self._heading = float(self._normalize_heading(heading))

    def set_heading_rad(self, heading: float) -> None:
        import math

        self.set_heading(math.degrees(heading))

    def set_coordinate(self, x: float, y: float) -> None:
        self.set_x(x)
        self.set_y(y)

    def set_coordinate_heading(self, x: float, y: float, heading: float) -> None:
        self.set_coordinate(x, y)
        self.set_heading(heading)

    # Utilities -----------------------------------------------------------
    def __str__(self) -> str:
        return (
            f"x:{self._round2(self._x)} y:{self._round2(self._y)} "
            f"heading:{self._round2(self._heading)}"
        )

    def print(self) -> None:  # noqa: A003 - mirror Java name
        print(str(self))

    def publish_coordinate(self) -> None:
        # Keep format identical to Java using a JSON array of one object
        coord = {
            "id": self._robot_id,
            "x": self.get_x(),
            "y": self.get_y(),
            "heading": self.get_heading(),
            "reality": "V",
        }
        data = [coord]

        import json

        self.robot_mqtt_client.publish("localization/update", json.dumps(data))

    # Internal helpers ----------------------------------------------------
    def _round2(self, v: float) -> float:
        return round(v * 100) / 100.0

    def _normalize_heading(self, heading: float) -> float:
        import math

        # normalize to [-180, 180]
        return heading - math.ceil(heading / 360.0 - 0.5) * 360.0
