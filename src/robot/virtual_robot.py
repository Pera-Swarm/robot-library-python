from __future__ import annotations

from .robot_base import Robot


class VirtualRobot(Robot):
    def __init__(self, id: int, x: float, y: float, heading: float):
        super().__init__(id, x, y, heading, "V")

    def loop(self) -> None:
        # To be implemented by user subclasses
        pass

    def sensor_interrupt(self, sensor: str, value: str) -> None:
        if sensor == "distance":
            print(f"Distance sensor interrupt on {self.id} with value {value}")
        elif sensor == "color":
            print(f"Color sensor interrupt on {self.id} with value {value}")
        elif sensor == "proximity":
            print(f"Proximity sensor interrupt on {self.id} with value {value}")
        else:
            print("Unknown sensor type")

    def communication_interrupt(self, msg: str) -> None:
        # To be implemented in subclass if desired
        pass
