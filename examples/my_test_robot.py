from __future__ import annotations

import threading
import time

from robot import MQTTSettings, VirtualRobot
from robot.interfaces import RobotState


class MyTestRobot(VirtualRobot):
    def setup(self) -> None:  # type: ignore[override]
        print("My Test Robot Started")
        super().setup()

    def loop(self) -> None:  # type: ignore[override]
        super().loop()
        if self.state == RobotState.RUN:
            print("Test")
            self.delay(1000)

    def communication_interrupt(self, msg: str) -> None:  # type: ignore[override]
        print(f"communicationInterrupt on {self.id} with msg:{msg}")


if __name__ == "__main__":
    # Configure MQTT (fill with your broker details)
    MQTTSettings.server = "localhost"
    MQTTSettings.port = 1883
    MQTTSettings.user_name = ""
    MQTTSettings.password = ""
    MQTTSettings.channel = "v1"

    robot = MyTestRobot(10, 0, 0, 90)
    t = threading.Thread(target=robot.run, daemon=True)
    t.start()

    # Example to send start after a short delay
    time.sleep(1)
    robot.start()
    t.join()
