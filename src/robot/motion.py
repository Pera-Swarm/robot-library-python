"""
Motion controller algorithms.
"""

import math
import time

# Assume wheel parameters (can be tuned to match your Java lib)
WHEEL_RADIUS = 1.0      # wheel radius in cm
WHEEL_BASE = 5.0        # distance between wheels in cm
MAX_SPEED = 100         # max motor speed in cm/s


class MotionController:
    """
    Dead-reckoning motion controller.
    Computes new positions and heading from motor speeds.
    """

    def __init__(self, coordinate, robot_mqtt, step_interval=0.1):
        """
        :param coordinate: Coordinate object to track robot pose
        :param robot_mqtt: RobotMqtt helper for publishing updates
        :param step_interval: simulation step interval in seconds
        """
        self.coordinate = coordinate
        self.robot_mqtt = robot_mqtt
        self.step_interval = step_interval

    # -------------------------------------------------------------------
    # Core motion update
    # -------------------------------------------------------------------

    def drive(self, left_speed, right_speed, duration):
        """
        Drive robot using left & right motor speeds for a duration.
        Updates position using dead-reckoning kinematics.

        :param left_speed: Left wheel speed (cm/s)
        :param right_speed: Right wheel speed (cm/s)
        :param duration: Duration in seconds
        """
        # Validate
        self._validate_speed(left_speed)
        self._validate_speed(right_speed)

        steps = int(duration / self.step_interval)
        for _ in range(steps):
            self._step(left_speed, right_speed, self.step_interval)
            self.robot_mqtt.publish_coordinate(self.coordinate)
            time.sleep(self.step_interval)

    def _step(self, vl, vr, dt):
        """Perform one integration step."""
        theta = math.radians(self.coordinate.heading)

        if abs(vl - vr) < 1e-6:
            # Straight line motion
            v = (vl + vr) / 2.0
            dx = v * math.cos(theta) * dt
            dy = v * math.sin(theta) * dt
            dtheta = 0
        else:
            # Differential drive arc
            R = (WHEEL_BASE / 2.0) * (vl + vr) / (vr - vl)
            omega = (vr - vl) / WHEEL_BASE  # angular velocity
            dtheta = omega * dt
            dx = R * (math.sin(theta + dtheta) - math.sin(theta))
            dy = -R * (math.cos(theta + dtheta) - math.cos(theta))

        # Update state
        self.coordinate.x += dx
        self.coordinate.y += dy
        self.coordinate.heading = (math.degrees(theta + dtheta)) % 360

    # -------------------------------------------------------------------
    # High-level helpers
    # -------------------------------------------------------------------

    def move_forward(self, distance, speed=50):
        """
        Move forward by a specific distance.
        """
        duration = distance / speed
        self.drive(speed, speed, duration)

    def move_backward(self, distance, speed=50):
        """
        Move backward by a specific distance.
        """
        duration = distance / speed
        self.drive(-speed, -speed, duration)

    def rotate(self, angle_deg, speed=30):
        """
        Rotate robot in place by angle (deg).
        Positive = left turn, Negative = right turn.
        """
        # Angular velocity: omega = (vr - vl) / WHEEL_BASE
        vl = -speed
        vr = speed
        omega = (vr - vl) / WHEEL_BASE
        duration = math.radians(abs(angle_deg)) / abs(omega)

        if angle_deg > 0:  # left turn
            self.drive(vl, vr, duration)
        else:              # right turn
            self.drive(vr, vl, duration)

    # -------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------

    def _validate_speed(self, speed):
        if abs(speed) > MAX_SPEED:
            raise ValueError(f"Speed {speed} exceeds maximum {MAX_SPEED}")
