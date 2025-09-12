"""Abstract Robot base class mirroring swarm.robot.Robot (Java).

Method names are provided in snake_case.
"""

from __future__ import annotations

import time
from typing import Optional

from robot.communication.directed_comm import DirectedCommunication
from robot.communication.simple_comm import SimpleCommunication
from robot.configs.mqtt_settings import MQTTSettings
from robot.helpers.coordinate import Coordinate
from robot.helpers.motion_controller import MotionController
from robot.helpers.robot_mqtt import RobotMQTT
from robot.indicators.neopixel import NeoPixel
from robot.interfaces import IRobotState, RobotState
from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.sensors.color import ColorSensor
from robot.sensors.distance import DistanceSensor
from robot.sensors.proximity import ProximitySensor


class Robot(IRobotState):
    # Sensors
    dist_sensor: DistanceSensor
    proximity_sensor: ProximitySensor
    color_sensor: ColorSensor

    # Communication
    simple_comm: SimpleCommunication
    directed_comm: DirectedCommunication

    # Output
    neo_pixel: NeoPixel

    # Helpers
    motion: MotionController
    robot_mqtt: RobotMQTT
    coordinates: Coordinate
    robot_mqtt_client: RobotMqttClient

    # Vars
    id: int
    reality: str
    state: RobotState = RobotState.WAIT

    def __init__(
        self,
        id: int,
        x: float,
        y: float,
        heading: float,
        reality: str,
    ):
        self.id = id
        self.reality = reality

        # Create mqtt client
        self.robot_mqtt_client = RobotMqttClient(
            MQTTSettings.server or "localhost",
            int(MQTTSettings.port),
            MQTTSettings.user_name or "",
            MQTTSettings.password or "",
            MQTTSettings.channel or "v1",
        )

        self.coordinates = Coordinate(id, x, y, heading, self.robot_mqtt_client)
        self.robot_mqtt = RobotMQTT(id, self.robot_mqtt_client, reality)

        # Request simulator to create robot instance
        self.robot_mqtt.robot_create(
            self.coordinates.get_x(),
            self.coordinates.get_y(),
            self.coordinates.get_heading(),
        )

        self.delay(1000)
        self.motion = MotionController(self.coordinates)

    # Lifecycle ---------------------------------------------------------
    def setup(self) -> None:
        # Setup each module
        self.dist_sensor = DistanceSensor(self, self.robot_mqtt_client)
        self.proximity_sensor = ProximitySensor(self, self.robot_mqtt_client)
        self.color_sensor = ColorSensor(self, self.robot_mqtt_client)

        self.neo_pixel = NeoPixel(self, self.robot_mqtt_client)

        self.simple_comm = SimpleCommunication(self.id, self.robot_mqtt_client)
        self.directed_comm = DirectedCommunication(self.id, self.robot_mqtt_client)

        self.coordinates.set_coordinate_heading(
            self.coordinates.get_x(),
            self.coordinates.get_y(),
            self.coordinates.get_heading(),
        )
        self.coordinates.publish_coordinate()

    def get_id(self) -> int:
        return self.id

    def run(self) -> None:
        self.setup()
        while True:
            begin_time = time.time() * 1000
            try:
                self.loop()
            except Exception as e:  # noqa: BLE001
                print(e)
            end_time = time.time() * 1000

            # Maintain ~1Hz loop rate as in Java implementation
            self.delay(int(max(0, 1000 - (end_time - begin_time))))

            try:
                self.handle_subscribe_queue()
            except Exception as e:  # noqa: BLE001
                print(e)

    # Subscription handler ----------------------------------------------
    def handle_subscribe_queue(self) -> None:
        while self.robot_mqtt_client.in_queue:
            m: Optional[MqttMsg] = self.robot_mqtt_client.in_queue_pop()
            if not m:
                continue
            tg0 = m.topic_groups[0] if m.topic_groups else ""
            if tg0 == "robot":
                self.robot_mqtt.handle_subscription(self, m)
            elif tg0 == "sensor":
                if len(m.topic_groups) > 1:
                    if m.topic_groups[1] == "distance":
                        self.dist_sensor.handle_subscription(self, m)
                    elif m.topic_groups[1] == "color":
                        self.color_sensor.handle_subscription(self, m)
                    elif m.topic_groups[1] == "proximity":
                        self.proximity_sensor.handle_subscription(self, m)
            elif tg0 == "localization":
                if m.topic == "localization/update/?":
                    self.coordinates.handle_subscription(self, m)
            elif tg0 == "comm":
                if len(m.topic_groups) > 2 and m.topic_groups[2] == "simple":
                    self.simple_comm.handle_subscription(self, m)
                else:
                    self.directed_comm.handle_subscription(self, m)
            elif tg0 == "output":
                if len(m.topic_groups) > 1 and m.topic_groups[1] == "NeoPixel":
                    self.neo_pixel.handle_subscription(self, m)

    # State handlers -----------------------------------------------------
    def start(self) -> None:
        print(f"Robot start on {self.id}")
        self.state = RobotState.RUN

    def stop(self) -> None:
        print(f"Robot stop on {self.id}")
        self.state = RobotState.WAIT

    def reset(self) -> None:
        print(f"Robot reset on {self.id}")
        self.state = RobotState.BEGIN

    # Utility ------------------------------------------------------------
    def delay(self, milliseconds: int) -> None:
        try:
            time.sleep(max(0, milliseconds) / 1000.0)
        except Exception:
            pass

    # Abstracts to implement in subclasses ------------------------------
    def loop(self) -> None:
        pass

    def sensor_interrupt(self, sensor: str, value: str) -> None:
        pass

    def communication_interrupt(self, msg: str) -> None:
        pass
