"""Interfaces mirroring the Java interfaces (snake_case in Python).

This module defines protocol-like interfaces and enums to preserve the design
from the Java implementation while remaining Pythonic.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from robot.mqtt.mqtt_msg import MqttMsg
    from robot.robot_base import Robot


class RobotState(Enum):
    WAIT = "WAIT"
    RUN = "RUN"
    BEGIN = "BEGIN"


@runtime_checkable
class IRobotState(Protocol):
    state: RobotState

    def loop(self) -> None: ...

    def sensor_interrupt(self, sensor: str, value: str) -> None: ...

    def communication_interrupt(self, msg: str) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def reset(self) -> None: ...


@runtime_checkable
class IMqttHandler(Protocol):
    def handle_subscription(self, r: "Robot", m: "MqttMsg") -> None: ...


__all__ = [
    "RobotState",
    "IRobotState",
    "IMqttHandler",
]
