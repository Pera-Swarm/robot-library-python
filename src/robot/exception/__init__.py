"""Exception types mirroring Java exceptions (slim wrappers)."""


class MotionControllerException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        print(f"Motion Error: {message}")


class MqttClientException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        print(f"MQTT Error: {message}")


class SensorException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        print(f"Sensor Error: {message}")


class ProximityException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        print(f"Proximity reading error: {message}")


class RGBColorException(Exception):
    def __init__(
        self,
        R: int | None = None,
        G: int | None = None,
        B: int | None = None,
    ):
        msg = f"Invalid RGB values: R={R}, G={G}, B={B}"
        super().__init__(msg)
        print(msg)


__all__ = [
    "MotionControllerException",
    "MqttClientException",
    "SensorException",
    "ProximityException",
    "RGBColorException",
]
