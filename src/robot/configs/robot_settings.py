"""Robot settings analogous to swarm.configs.RobotSettings (Java)."""


class RobotSettings:
    ROBOT_SPEED_MAX: int = 255
    ROBOT_SPEED_MIN: int = 50

    ROBOT_RADIUS: int = 6  # in cm
    ROBOT_WIDTH: int = 12  # in cm
    ROBOT_WHEEL_RADIUS: float = 3.5  # in cm

    # 0: no logs (TODO: implement levels)
    ROBOT_LOG_LEVEL: int = 0


__all__ = ["RobotSettings"]
