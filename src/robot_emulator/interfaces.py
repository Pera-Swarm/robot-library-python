from abc import ABC, abstractmethod
from enum import Enum


class IMqttHandler(ABC):
    @abstractmethod
    def handle_subscription(self, robot, message) -> None:
        pass


class RobotState(Enum):
    WAIT = "WAIT"
    RUN = "RUN"
    BEGIN = "BEGIN"


class IRobotState(ABC):
    
    @abstractmethod
    def loop(self) -> None:
        pass

    @abstractmethod
    def sensor_interrupt(self, sensor: str, value: str) -> None:
        pass

    @abstractmethod
    def communication_interrupt(self, msg: str) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass
