from __future__ import annotations

import math
import time

from robot.configs.robot_settings import RobotSettings
from robot.exception import MotionControllerException
from robot.helpers.coordinate import Coordinate


class MotionController:
    # This is the maximum duration allowed to coordinate calculation
    _MAX_DURATION = 100

    CM_2_MM = 10
    SEC_2_MS = 1000

    # Additional delays for simulation time
    ADDITIONAL_DELAY = 500

    # Match cm/s speed
    SPEED_FACTOR = 0.1

    def __init__(self, coordinate: Coordinate | None = None):
        if coordinate is None:
            # Lightweight fallback coordinate for tests or standalone use
            class _StubCoord:
                def __init__(self):
                    self._x = 0.0
                    self._y = 0.0
                    self._h = 0.0

                def get_x(self):
                    return self._x

                def get_y(self):
                    return self._y

                def get_heading(self):
                    return self._h

                def get_heading_rad(self):
                    return math.radians(self._h)

                def set_coordinate_heading(self, x, y, h):
                    self._x, self._y, self._h = x, y, h

                def publish_coordinate(self):
                    pass

            coordinate = _StubCoord()  # type: ignore[assignment]
        self.c = coordinate  # type: ignore[assignment]

    # Wrappers -----------------------------------------------------------
    def move(
        self, left_speed: int, right_speed: int, duration: int | float | None = None
    ) -> None:
        if duration is None:
            duration = self._MAX_DURATION
        self._move(left_speed, right_speed, float(duration))

    def rotate(self, speed: int, duration: int | float | None = None) -> None:
        if duration is None:
            duration = self._MAX_DURATION
        self._rotate(speed, float(duration))

    def rotate_radians(self, speed: int, radians: float) -> None:
        self.rotate_degree(speed, math.degrees(radians))

    def rotate_degree(self, speed: int, degree: float) -> None:
        try:
            if degree == 0 or degree < -180 or degree > 180:
                raise MotionControllerException(
                    "Degree should in range [-180, 180], except 0"
                )
            if speed < RobotSettings.ROBOT_SPEED_MIN:
                raise MotionControllerException(
                    "Speed should be greater than ROBOT_SPEED_MIN"
                )

            sign = int(degree / abs(degree))
            distance = (
                2 * math.pi * RobotSettings.ROBOT_RADIUS * (abs(degree) / 360)
            ) * self.CM_2_MM
            duration = float(distance / abs(speed)) * self.SEC_2_MS
            self._debug(f"Sign: {sign} Distance: {distance} Duration: {duration}")
            self._rotate(sign * speed, duration)
        except MotionControllerException:  # noqa: F841
            pass

    # Core movement ------------------------------------------------------
    def _rotate(self, speed: int, duration: float) -> None:
        self._move(speed, -1 * speed, duration)

    def _move(self, left_speed: int, right_speed: int, duration: float) -> None:
        if not (
            self._is_speed_in_range(left_speed) and self._is_speed_in_range(right_speed)
        ):
            try:
                raise MotionControllerException(
                    "One of the provided speeds is out of range in move() function"
                )
            except MotionControllerException:
                return

        # step interval in ms, break the duration into slices
        step_interval = 100
        cumulative_interval = 0
        steps = int(duration // step_interval) if duration > 0 else 0

        for _ in range(steps):
            dL = left_speed * self.SPEED_FACTOR * (step_interval / 1000.0)
            dR = right_speed * self.SPEED_FACTOR * (step_interval / 1000.0)
            d = (dL + dR) / 2.0
            h = self.c.get_heading_rad()

            x = self.c.get_x() + d * math.cos(h)
            y = self.c.get_y() + d * math.sin(h)
            heading = self.c.get_heading_rad() + (dR - dL) / (RobotSettings.ROBOT_WIDTH)

            self.c.set_coordinate_heading(x, y, math.degrees(heading))

            cumulative_interval += step_interval
            if cumulative_interval >= self.ADDITIONAL_DELAY:
                self._debug(f"Adding extra delay of {self.ADDITIONAL_DELAY}")
                self._delay(self.ADDITIONAL_DELAY)
                self.c.publish_coordinate()
                cumulative_interval -= self.ADDITIONAL_DELAY

        # Round to nearest int
        self.c.set_coordinate_heading(
            round(self.c.get_x()), round(self.c.get_y()), round(self.c.get_heading())
        )
        self.c.publish_coordinate()

    # Helpers ------------------------------------------------------------
    def _is_speed_in_range(self, speed: int) -> bool:
        if speed > 0:
            return (
                RobotSettings.ROBOT_SPEED_MIN <= speed <= RobotSettings.ROBOT_SPEED_MAX
            )
        elif speed < 0:
            return (
                -RobotSettings.ROBOT_SPEED_MAX
                <= speed
                <= -RobotSettings.ROBOT_SPEED_MIN
            )
        return True  # 0 acceptable

    def _delay(self, duration_ms: int) -> None:
        time.sleep(max(0, duration_ms) / 1000.0)

    @staticmethod
    def _debug(msg: str, level: int = 0) -> None:
        if level > 0:
            print(f"[DEBUG]\t{msg}")
