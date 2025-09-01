"""Coordinate tracking helper."""

import math
from dataclasses import dataclass
from typing import Tuple, Optional


def _wrap_deg(angle_deg: float) -> float:
    # Normalize to [0, 360)
    a = angle_deg % 360.0
    if a < 0:
        a += 360.0
    return a


@dataclass
class Coordinate:
    """
    Pose container and odometry utilities.
    Units: centimeters for x,y; degrees for heading (0..360).
    Heading 0 deg = +X axis; positive angles rotate CCW.
    """
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0  # degrees

    # ------------- Odometry updates -------------

    def update_from_wheel_speeds(
        self, v_l: float, v_r: float, dt: float, wheel_base: float
    ):
        """
        Integrate pose from left/right linear speeds (cm/s) over dt (s).
        wheel_base is wheel separation (cm).
        """
        theta = math.radians(self.heading)
        if abs(v_l - v_r) < 1e-9:
            v = 0.5 * (v_l + v_r)
            self.x += v * math.cos(theta) * dt
            self.y += v * math.sin(theta) * dt
            # heading unchanged
        else:
            R = (wheel_base / 2.0) * (v_l + v_r) / (v_r - v_l)
            omega = (v_r - v_l) / wheel_base
            dtheta = omega * dt
            self.x += R * (math.sin(theta + dtheta) - math.sin(theta))
            self.y += -R * (math.cos(theta + dtheta) - math.cos(theta))
            self.heading = _wrap_deg(math.degrees(theta + dtheta))
        # If straight case, ensure heading normalized too
        self.heading = _wrap_deg(self.heading)
        # Matches canonical differential-drive odometry for ICC motion. [4][1]

    def set_pose(self, x: float, y: float, heading_deg: float):
        self.x = float(x)
        self.y = float(y)
        self.heading = _wrap_deg(float(heading_deg))

    def apply_delta(self, dx: float, dy: float, dtheta_deg: float):
        """Apply a small world-frame delta to the pose."""
        self.x += float(dx)
        self.y += float(dy)
        self.heading = _wrap_deg(self.heading + float(dtheta_deg))

    # ------------- Frame conversions -------------

    def world_to_robot(self, wx: float, wy: float) -> Tuple[float, float]:
        """
        Convert a world point to robot-centric coordinates.
        """
        dx = wx - self.x
        dy = wy - self.y
        theta = math.radians(self.heading)
        rx = dx * math.cos(-theta) - dy * math.sin(-theta)
        ry = dx * math.sin(-theta) + dy * math.cos(-theta)
        return rx, ry

    def robot_to_world(self, rx: float, ry: float) -> Tuple[float, float]:
        """
        Convert a robot-centric point to world coordinates.
        """
        theta = math.radians(self.heading)
        wx = rx * math.cos(theta) - ry * math.sin(theta) + self.x
        wy = rx * math.sin(theta) + ry * math.cos(theta) + self.y
        return wx, wy

    # ------------- Publishing -------------

    def publish(self, robot_mqtt, robot_id: Optional[int] = None):
        """
        Publish pose via the RobotMQTT helper. If a different robot_id is
        required by the application, pass it; otherwise RobotMQTT will use
        its configured id.
        """
        # RobotMQTT.publish_coordinate reads self.x/y/heading by default.
        robot_mqtt.publish_coordinate(self)
